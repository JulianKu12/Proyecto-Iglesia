from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
import shutil
import tempfile

from accounts.models import Usuario
from core.permissions import ROL_ADMINISTRADOR, ROL_PASTOR

from .models import ConfiguracionIglesia


class InstitucionTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.mkdtemp()
        self.media_settings = override_settings(MEDIA_ROOT=self.media_dir)
        self.media_settings.enable()
        self.addCleanup(self.media_settings.disable)
        self.addCleanup(shutil.rmtree, self.media_dir)

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

    def test_al_reemplazar_logotipo_se_elimina_el_anterior(self):
        primero = SimpleUploadedFile("primero.png", b"contenido primero", content_type="image/png")
        configuracion = ConfiguracionIglesia.objects.create(nombre="Iglesia", logotipo=primero)
        nombre_anterior = configuracion.logotipo.name
        self.assertTrue(configuracion.logotipo.storage.exists(nombre_anterior))

        segundo = SimpleUploadedFile("segundo.png", b"contenido segundo", content_type="image/png")
        configuracion.logotipo = segundo
        configuracion.save()

        self.assertFalse(configuracion.logotipo.storage.exists(nombre_anterior))
        self.assertTrue(configuracion.logotipo.storage.exists(configuracion.logotipo.name))

    def test_al_quitar_logotipo_se_elimina_el_archivo(self):
        archivo = SimpleUploadedFile("logo.png", b"contenido logo", content_type="image/png")
        configuracion = ConfiguracionIglesia.objects.create(nombre="Iglesia", logotipo=archivo)
        nombre = configuracion.logotipo.name

        configuracion.logotipo = None
        configuracion.save()

        self.assertFalse(configuracion.logotipo.storage.exists(nombre))
