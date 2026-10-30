from datetime import date, timedelta
import json

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from core.permissions import ROL_ADMINISTRADOR, ROL_COORDINADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_TESORERO
from ministries.models import Ministerio

from .models import Evento


class EventosTests(TestCase):
    def setUp(self):
        self.usuarios = {}
        for rol in (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_TESORERO, ROL_COORDINADOR):
            usuario = Usuario.objects.create_user(f"{rol.lower()}@eventos.test", "secreto123", nombre=rol)
            usuario.groups.add(Group.objects.get(name=rol))
            self.usuarios[rol] = usuario
        self.ministerio = Ministerio.objects.create(nombre="Música", coordinador=self.usuarios[ROL_COORDINADOR])
        self.otro = Ministerio.objects.create(nombre="Jóvenes", coordinador=self.usuarios[ROL_PASTOR])
        self.evento = Evento.objects.create(titulo="Culto", tipo=Evento.TIPO_RELIGIOSO, fecha=date.today() + timedelta(days=2), hora="10:00", ministerio=self.ministerio)
        self.cancelado = Evento.objects.create(titulo="Cancelado", tipo=Evento.TIPO_ADMINISTRATIVO, fecha=date.today() + timedelta(days=3), hora="12:00", estado=Evento.ESTADO_CANCELADO)

    def test_permisos_y_calendario(self):
        for rol in (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_TESORERO, ROL_COORDINADOR):
            self.client.force_login(self.usuarios[rol])
            self.assertEqual(self.client.get(reverse("eventos")).status_code, 200)
            self.assertEqual(self.client.get(reverse("evento_detalle", args=[self.evento.pk])).status_code, 200)
            response = self.client.get(reverse("calendario_datos"), {"start": str(date.today()), "end": str(date.today() + timedelta(days=10))})
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(json.loads(response.content), list)
        self.client.force_login(self.usuarios[ROL_COORDINADOR])
        self.assertEqual(self.client.get(reverse("evento_detalle", args=[self.cancelado.pk])).status_code, 404)
        self.client.force_login(self.usuarios[ROL_TESORERO])
        self.assertEqual(self.client.get(reverse("evento_crear")).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("eventos")).status_code, 302)

    def test_cancelar_reactivar_y_no_editar_cancelado(self):
        self.client.force_login(self.usuarios[ROL_ADMINISTRADOR])
        self.client.post(reverse("evento_cancelar", args=[self.evento.pk]), {"motivo_cancelacion": "Por lluvia"})
        self.evento.refresh_from_db()
        self.assertEqual(self.evento.estado, Evento.ESTADO_CANCELADO)
        self.assertEqual(self.client.get(reverse("evento_editar", args=[self.evento.pk])).status_code, 302)
        self.client.post(reverse("evento_reactivar", args=[self.evento.pk]))
        self.evento.refresh_from_db()
        self.assertEqual(self.evento.estado, Evento.ESTADO_PROGRAMADO)

    def test_coordinador_solo_ve_eventos_de_sus_ministerios(self):
        ajeno = Evento.objects.create(titulo="Ajeno", tipo=Evento.TIPO_RELIGIOSO, fecha=date.today() + timedelta(days=5), hora="10:00", ministerio=self.otro)
        self.client.force_login(self.usuarios[ROL_COORDINADOR])
        response = self.client.get(reverse("eventos"), {"alcance": "todos"})
        self.assertContains(response, "Culto")
        self.assertNotContains(response, "Ajeno")
        self.assertEqual(self.client.get(reverse("evento_detalle", args=[ajeno.pk])).status_code, 404)
