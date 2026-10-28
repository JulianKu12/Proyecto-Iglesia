from datetime import date

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from core.permissions import (
    ROL_ADMINISTRADOR,
    ROL_COORDINADOR,
    ROL_PASTOR,
    ROL_SECRETARIO,
    ROL_TESORERO,
)

from .models import Miembro


class MiembrosPermisosYFiltrosTests(TestCase):
    def setUp(self):
        self.miembro = Miembro.objects.create(nombre_completo="José Álvarez", fecha_ingreso=date.today())
        self.inactivo = Miembro.objects.create(nombre_completo="Ana Demo", fecha_ingreso=date.today(), activo=False)
        self.usuarios = {}
        for rol in (ROL_ADMINISTRADOR, ROL_SECRETARIO, ROL_PASTOR, ROL_TESORERO, ROL_COORDINADOR):
            usuario = Usuario.objects.create_user(f"{rol.lower()}@test.local", "secreto123", nombre=rol)
            usuario.groups.add(Group.objects.get(name=rol))
            self.usuarios[rol] = usuario

    def test_permisos_por_rol(self):
        for rol in (ROL_ADMINISTRADOR, ROL_SECRETARIO, ROL_PASTOR, ROL_TESORERO):
            self.client.force_login(self.usuarios[rol])
            self.assertEqual(self.client.get(reverse("miembros")).status_code, 200)
            self.assertEqual(self.client.get(reverse("miembro_detalle", args=[self.miembro.pk])).status_code, 200)
        for rol in (ROL_ADMINISTRADOR, ROL_SECRETARIO):
            self.client.force_login(self.usuarios[rol])
            self.assertEqual(self.client.get(reverse("miembro_crear")).status_code, 200)
            self.assertEqual(self.client.get(reverse("miembro_editar", args=[self.miembro.pk])).status_code, 200)
            self.assertEqual(
                self.client.post(reverse("miembro_estado", args=[self.miembro.pk]), {"accion": "desactivar"}).status_code,
                302,
            )
        self.client.force_login(self.usuarios[ROL_PASTOR])
        self.assertEqual(self.client.get(reverse("miembro_crear")).status_code, 403)
        self.client.force_login(self.usuarios[ROL_COORDINADOR])
        self.assertEqual(self.client.get(reverse("miembros")).status_code, 403)
        self.assertEqual(self.client.get(reverse("miembro_detalle", args=[self.miembro.pk])).status_code, 403)

    def test_desactivar_conserva_registro_y_lo_saca_de_activos(self):
        self.client.force_login(self.usuarios[ROL_ADMINISTRADOR])
        self.client.post(reverse("miembro_estado", args=[self.miembro.pk]), {"accion": "desactivar"})
        self.miembro.refresh_from_db()
        self.assertFalse(self.miembro.activo)
        self.assertTrue(Miembro.objects.filter(pk=self.miembro.pk).exists())
        respuesta = self.client.get(reverse("miembros"))
        self.assertNotContains(respuesta, "José Álvarez")
        respuesta = self.client.get(reverse("miembros") + "?estado=inactivos")
        self.assertContains(respuesta, "José Álvarez")

    def test_busqueda_sin_acentos_y_filtros(self):
        self.client.force_login(self.usuarios[ROL_PASTOR])
        respuesta = self.client.get(reverse("miembros") + "?q=jose")
        self.assertContains(respuesta, "José Álvarez")
        self.assertNotContains(respuesta, "Ana Demo")
        respuesta = self.client.get(reverse("miembros") + "?estado=todos")
        self.assertContains(respuesta, "Ana Demo")
