from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.core import mail
from django.test import TestCase, override_settings
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

    def test_protecciones_del_administrador(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse("usuario_desactivar", args=[self.admin.pk]))
        self.assertRedirects(respuesta, reverse("usuarios"))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.activo)
        respuesta = self.client.post(
            reverse("usuario_editar", args=[self.admin.pk]),
            {
                "correo": self.admin.correo,
                "nombre": self.admin.nombre,
                "activo": "on",
                "rol": "Pastor",
                "miembro": "",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "No puedes cambiar tu propio rol")

    def test_no_se_puede_dejar_sin_administrador_activo(self):
        segundo = Usuario.objects.create_user("segundo-admin@test.local", "secreto123", nombre="Segundo")
        segundo.groups.add(Group.objects.get(name=ROL_ADMINISTRADOR))
        self.client.force_login(self.admin)
        segundo.activo = False
        segundo.save(update_fields=("activo",))
        respuesta = self.client.post(reverse("usuario_desactivar", args=[self.admin.pk]))
        self.assertRedirects(respuesta, reverse("usuarios"))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.activo)

    def test_formulario_muestra_errores_de_contraseñas(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            reverse("usuario_crear"),
            {
                "correo": "nuevo@test.local",
                "nombre": "",
                "activo": "on",
                "rol": ROL_PASTOR,
                "miembro": "",
                "password1": "abc",
                "password2": "def",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Las contraseñas no coinciden")
        self.assertContains(respuesta, "is-invalid")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_recuperacion_de_contrasena_completa(self):
        self.client.post(reverse("password_reset"), {"email": self.admin.correo})
        self.assertEqual(len(mail.outbox), 1)
        enlace = next(line for line in mail.outbox[0].body.splitlines() if "password-reset/" in line)
        respuesta = self.client.get(enlace, follow=True)
        self.assertEqual(respuesta.status_code, 200)
        token_url = respuesta.request["PATH_INFO"]
        respuesta = self.client.post(
            token_url,
            {"new_password1": "NuevaClave123!", "new_password2": "NuevaClave123!"},
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(self.admin.__class__.objects.get(pk=self.admin.pk).check_password("NuevaClave123!"))

    def test_cache_logout_y_errores_personalizados(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse("usuarios"))
        self.assertEqual(respuesta.headers["Cache-Control"], "no-store, no-cache, private")
        self.assertEqual(self.client.get("/ruta-inexistente/").status_code, 404)
        self.assertContains(self.client.get("/ruta-inexistente/"), "Página no encontrada", status_code=404)
        self.assertEqual(self.client.get(reverse("usuario_desactivar", args=[self.usuario.pk])).status_code, 405)
        self.assertEqual(self.client.post(reverse("logout")).status_code, 302)


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

    def test_403_personalizado(self):
        self.client.force_login(self.pastor)
        respuesta = self.client.get(reverse("usuarios"))
        self.assertContains(respuesta, "No tienes permisos", status_code=403)

    def test_usuario_desactivado_no_puede_iniciar_sesion(self):
        self.pastor.activo = False
        self.pastor.save()
        self.assertFalse(self.client.login(correo="pastor@iglesia.test", password="secreto123"))
