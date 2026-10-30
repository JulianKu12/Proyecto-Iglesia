from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from core.permissions import ROL_ADMINISTRADOR, ROL_PASTOR

from .models import ConfiguracionIglesia


class InstitucionTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user("admin@test.local", "secreto123", nombre="Admin")
        self.admin.groups.add(Group.objects.get(name=ROL_ADMINISTRADOR))
        self.pastor = Usuario.objects.create_user("pastor@test.local", "secreto123", nombre="Pastor")
        self.pastor.groups.add(Group.objects.get(name=ROL_PASTOR))

    def test_solo_administrador_puede_editar(self):
        self.client.force_login(self.pastor)
        self.assertEqual(self.client.get(reverse("institucion")).status_code, 403)
        self.assertEqual(self.client.post(reverse("institucion"), {}).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("institucion")).status_code, 200)
        self.assertEqual(
            self.client.post(
                reverse("institucion"),
                {
                    "nombre": "Iglesia de Prueba",
                    "direccion": "",
                    "telefono": "",
                    "correo_contacto": "",
                    "horarios-TOTAL_FORMS": "1",
                    "horarios-INITIAL_FORMS": "0",
                    "horarios-MIN_NUM_FORMS": "0",
                    "horarios-MAX_NUM_FORMS": "100",
                },
            ).status_code,
            302,
        )
        self.assertEqual(ConfiguracionIglesia.objects.count(), 1)

    def test_solo_existe_una_configuracion(self):
        ConfiguracionIglesia.objects.create(nombre="Primera")
        with self.assertRaises(IntegrityError):
            ConfiguracionIglesia.objects.create(nombre="Segunda")

    def test_fila_nueva_no_muestra_eliminar_y_guardada_si(self):
        configuracion = ConfiguracionIglesia.objects.create(nombre="Iglesia")
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse("institucion"))
        self.assertNotContains(respuesta, 'name="horarios-0-DELETE"')
        configuracion.horarios.create(dia_semana=6, hora="10:00", nombre="Culto")
        respuesta = self.client.get(reverse("institucion"))
        self.assertContains(respuesta, 'name="horarios-0-DELETE"')
