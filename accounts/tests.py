from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import Usuario
from core.permissions import ROL_ADMINISTRADOR, ROL_PASTOR
from members.models import Miembro


class VinculoUsuarioMiembroTests(TestCase):
    def test_usuario_puede_vincularse_y_un_miembro_no_se_repite(self):
        miembro = Miembro.objects.create(nombre_completo="Miembro Vinculable", fecha_ingreso="2026-01-01")
        primero = Usuario.objects.create_user("primero@iglesia.test", "secreto123", nombre="Primero", miembro=miembro)
        self.assertEqual(primero.miembro, miembro)
        with self.assertRaises(IntegrityError):
            Usuario.objects.create_user("segundo@iglesia.test", "secreto123", nombre="Segundo", miembro=miembro)


class RutasUsuariosTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user("admin-rutas@test.local", "secreto123", nombre="Admin")
        self.admin.groups.add(Group.objects.get(name=ROL_ADMINISTRADOR))
        self.usuario = Usuario.objects.create_user("usuario-rutas@test.local", "secreto123", nombre="Usuario")

    def test_reactivar_usuario_desde_la_aplicacion(self):
        self.usuario.activo = False
        self.usuario.save(update_fields=("activo",))
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse("usuario_reactivar", args=[self.usuario.pk]))
        self.assertRedirects(respuesta, reverse("usuarios"))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.activo)

    def test_solo_administrador_accede_a_todas_las_rutas_de_usuarios(self):
        pastor = Usuario.objects.create_user("pastor-rutas@test.local", "secreto123", nombre="Pastor")
        pastor.groups.add(Group.objects.get(name=ROL_PASTOR))
        rutas = (
            ("usuarios", "get", {}),
            ("usuario_crear", "get", {}),
            ("usuario_editar", "get", {"args": [self.usuario.pk]}),
            ("usuario_desactivar", "post", {"args": [self.usuario.pk]}),
            ("usuario_reactivar", "post", {"args": [self.usuario.pk]}),
        )
        self.client.force_login(pastor)
        for nombre, metodo, opciones in rutas:
            respuesta = getattr(self.client, metodo)(reverse(nombre, **opciones))
            self.assertEqual(respuesta.status_code, 403, nombre)

    def test_sin_sesion_va_al_login_de_la_aplicacion(self):
        respuesta = self.client.get(reverse("usuarios"))
        self.assertRedirects(respuesta, f"{reverse('login')}?next={reverse('usuarios')}")

    def test_panel_django_admin_solo_acepta_superusuarios(self):
        staff = Usuario.objects.create_user("staff@test.local", "secreto123", nombre="Staff", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get("/admin/").status_code, 302)
        superusuario = Usuario.objects.create_superuser("super@test.local", "secreto123", nombre="Super")
        self.client.force_login(superusuario)
        self.assertEqual(self.client.get("/admin/").status_code, 200)


class AutenticacionYRolesTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user("admin@iglesia.test", "secreto123", nombre="Admin")
        self.admin.groups.add(Group.objects.get(name=ROL_ADMINISTRADOR))
        self.pastor = Usuario.objects.create_user("pastor@iglesia.test", "secreto123", nombre="Pastor")
        self.pastor.groups.add(Group.objects.get(name=ROL_PASTOR))

    def test_usuario_sin_sesion_es_redirigido_al_login(self):
        respuesta = self.client.get(reverse("inicio"))
        self.assertRedirects(respuesta, f"{reverse('login')}?next={reverse('inicio')}")

    def test_solo_administrador_accede_a_usuarios(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("usuarios")).status_code, 200)
        self.client.force_login(self.pastor)
        self.assertEqual(self.client.get(reverse("usuarios")).status_code, 403)

    def test_usuario_desactivado_no_puede_iniciar_sesion(self):
        self.pastor.activo = False
        self.pastor.save()
        self.assertFalse(self.client.login(correo="pastor@iglesia.test", password="secreto123"))
