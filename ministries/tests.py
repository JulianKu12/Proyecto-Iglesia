from datetime import date

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from core.permissions import ROL_ADMINISTRADOR, ROL_COORDINADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_TESORERO
from members.models import Miembro

from .models import Ministerio


class MinisteriosTests(TestCase):
    def setUp(self):
        self.miembro = Miembro.objects.create(nombre_completo="Miembro Activo", fecha_ingreso=date.today())
        self.otro = Miembro.objects.create(nombre_completo="Otro Activo", fecha_ingreso=date.today())
        self.usuarios = {}
        for rol in (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_TESORERO, ROL_COORDINADOR):
            usuario = Usuario.objects.create_user(f"{rol.lower()}@ministerios.test", "secreto123", nombre=rol)
            usuario.groups.add(Group.objects.get(name=rol))
            self.usuarios[rol] = usuario
        self.propio = Ministerio.objects.create(nombre="Música", coordinador=self.usuarios[ROL_COORDINADOR])
        self.ajeno = Ministerio.objects.create(nombre="Jóvenes", coordinador=self.usuarios[ROL_PASTOR])
        self.propio.miembros.add(self.miembro)

    def test_permisos_por_rol(self):
        for rol in (ROL_ADMINISTRADOR, ROL_SECRETARIO):
            self.client.force_login(self.usuarios[rol])
            self.assertEqual(self.client.get(reverse("ministerios")).status_code, 200)
            self.assertEqual(self.client.get(reverse("ministerio_crear")).status_code, 200)
        self.client.force_login(self.usuarios[ROL_PASTOR])
        self.assertEqual(self.client.get(reverse("ministerios")).status_code, 200)
        self.assertEqual(self.client.get(reverse("ministerio_crear")).status_code, 403)
        self.client.force_login(self.usuarios[ROL_COORDINADOR])
        self.assertEqual(self.client.get(reverse("ministerios")).status_code, 200)
        self.assertEqual(self.client.get(reverse("ministerio_detalle", args=[self.propio.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("ministerio_detalle", args=[self.ajeno.pk])).status_code, 404)
        self.client.force_login(self.usuarios[ROL_TESORERO])
        self.assertEqual(self.client.get(reverse("ministerios")).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("ministerios")).status_code, 302)

    def test_nombre_unico_sin_distinguir_mayusculas(self):
        self.client.force_login(self.usuarios[ROL_ADMINISTRADOR])
        response = self.client.post(reverse("ministerio_crear"), {"nombre": "MÚSICA", "descripcion": "", "activo": "on"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe un ministerio con ese nombre.")

    def test_formulario_solo_ofrece_coordinadores_activos(self):
        response = self.client.get(reverse("ministerio_crear"))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.usuarios[ROL_ADMINISTRADOR])
        response = self.client.get(reverse("ministerio_crear"))
        self.assertContains(response, self.usuarios[ROL_COORDINADOR].correo)
        self.assertNotContains(response, self.usuarios[ROL_PASTOR].correo)

    def test_integrantes_y_desactivacion_no_borran(self):
        self.client.force_login(self.usuarios[ROL_ADMINISTRADOR])
        response = self.client.post(reverse("ministerio_integrantes", args=[self.propio.pk]), {"miembros": [self.otro.pk]})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.propio.miembros.filter(pk=self.otro.pk).exists())
        self.client.post(reverse("ministerio_quitar_integrante", args=[self.propio.pk, self.otro.pk]))
        self.otro.refresh_from_db()
        self.assertTrue(self.otro.activo)
        self.assertFalse(self.propio.miembros.filter(pk=self.otro.pk).exists())
        self.client.post(reverse("ministerio_estado", args=[self.propio.pk]), {"accion": "desactivar"})
        self.propio.refresh_from_db()
        self.assertFalse(self.propio.activo)
        self.assertTrue(self.propio.miembros.filter(pk=self.miembro.pk).exists())

    def test_desactivar_coordinador_deja_ministerios_sin_coordinador(self):
        admin = self.usuarios[ROL_ADMINISTRADOR]
        self.client.force_login(admin)
        response = self.client.post(
            reverse("usuario_desactivar", args=[self.usuarios[ROL_COORDINADOR].pk]),
            {"accion": "desactivar"},
        )
        self.assertEqual(response.status_code, 302)
        self.propio.refresh_from_db()
        self.assertIsNone(self.propio.coordinador)
