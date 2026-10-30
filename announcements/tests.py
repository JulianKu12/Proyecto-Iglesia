from datetime import date, timedelta

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from core.permissions import ROL_ADMINISTRADOR, ROL_COORDINADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_TESORERO

from .models import Anuncio


class AnunciosTests(TestCase):
    def setUp(self):
        self.usuarios = {}
        for rol in (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_TESORERO, ROL_COORDINADOR):
            usuario = Usuario.objects.create_user(f"{rol.lower()}@anuncios.test", "secreto123", nombre=rol)
            usuario.groups.add(Group.objects.get(name=rol))
            self.usuarios[rol] = usuario
        self.importante = Anuncio.objects.create(titulo="Aviso importante", contenido="Texto", importante=True, autor=self.usuarios[ROL_ADMINISTRADOR])
        Anuncio.objects.create(titulo="Programado", contenido="Futuro", fecha_publicacion=date.today() + timedelta(days=2), autor=self.usuarios[ROL_ADMINISTRADOR])
        Anuncio.objects.create(titulo="Vencido", contenido="Viejo", vigente_hasta=date.today() - timedelta(days=1), autor=self.usuarios[ROL_ADMINISTRADOR])

    def test_visibilidad_publica_y_gestion_por_rol(self):
        self.client.force_login(self.usuarios[ROL_TESORERO])
        response = self.client.get(reverse("anuncios"))
        self.assertContains(response, "Aviso importante")
        self.assertNotContains(response, "Programado")
        self.assertNotContains(response, "Vencido")
        self.assertEqual(self.client.get(reverse("anuncios_gestion")).status_code, 403)
        for rol in (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO):
            self.client.force_login(self.usuarios[rol])
            self.assertEqual(self.client.get(reverse("anuncios_gestion")).status_code, 200)
            self.assertEqual(self.client.get(reverse("anuncio_crear")).status_code, 200)

    def test_eliminar_solo_por_post(self):
        self.client.force_login(self.usuarios[ROL_ADMINISTRADOR])
        self.assertEqual(self.client.get(reverse("anuncio_eliminar", args=[self.importante.pk])).status_code, 405)
        self.client.post(reverse("anuncio_eliminar", args=[self.importante.pk]))
        self.assertFalse(Anuncio.objects.filter(pk=self.importante.pk).exists())

    def test_bloques_de_inicio(self):
        self.client.force_login(self.usuarios[ROL_COORDINADOR])
        response = self.client.get(reverse("inicio"))
        self.assertContains(response, "Próximos eventos")
        self.assertContains(response, "Avisos importantes")
