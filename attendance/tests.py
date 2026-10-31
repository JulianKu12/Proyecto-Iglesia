from datetime import date, timedelta
import json

from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from core.permissions import ROL_ADMINISTRADOR, ROL_COORDINADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_TESORERO
from events.models import Evento
from members.models import Miembro
from ministries.models import Ministerio

from .models import Asistencia
from .services import rango_mes, resumen_periodo, semana_de


class AsistenciaTests(TestCase):
    def setUp(self):
        self.miembro = Miembro.objects.create(nombre_completo="Ana Activa", fecha_ingreso=date.today())
        self.otro = Miembro.objects.create(nombre_completo="Bruno Activo", fecha_ingreso=date.today())
        self.inactivo = Miembro.objects.create(nombre_completo="Carla Histórica", fecha_ingreso=date.today(), activo=False)
        self.usuarios = {}
        for rol in (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_TESORERO, ROL_COORDINADOR):
            usuario = Usuario.objects.create_user(f"{rol.lower()}@asistencia.test", "secreto123", nombre=rol)
            usuario.groups.add(Group.objects.get(name=rol))
            self.usuarios[rol] = usuario
        self.ministerio = Ministerio.objects.create(nombre="Música", coordinador=self.usuarios[ROL_COORDINADOR])
        self.ministerio.miembros.add(self.miembro)
        self.evento = Evento.objects.create(
            titulo="Culto de prueba",
            tipo=Evento.TIPO_RELIGIOSO,
            fecha=date.today(),
            hora="10:00",
            ministerio=self.ministerio,
        )
        self.futuro = Evento.objects.create(
            titulo="Evento futuro",
            tipo=Evento.TIPO_RELIGIOSO,
            fecha=date.today() + timedelta(days=1),
            hora="10:00",
            ministerio=self.ministerio,
        )
        self.cancelado = Evento.objects.create(
            titulo="Evento cancelado",
            tipo=Evento.TIPO_RELIGIOSO,
            fecha=date.today(),
            hora="12:00",
            estado=Evento.ESTADO_CANCELADO,
        )

    def login(self, rol):
        self.client.force_login(self.usuarios[rol])

    def test_permisos_por_rol_y_sin_sesion(self):
        rutas = ("asistencia_registrar", "asistencia_historial", "asistencia_resumen")
        for rol in (ROL_ADMINISTRADOR, ROL_SECRETARIO, ROL_COORDINADOR):
            self.login(rol)
            for ruta in rutas:
                self.assertEqual(self.client.get(reverse(ruta)).status_code, 200)
        self.login(ROL_PASTOR)
        self.assertEqual(self.client.get(reverse("asistencia_registrar")).status_code, 403)
        self.assertEqual(self.client.get(reverse("asistencia_historial")).status_code, 200)
        self.assertEqual(self.client.get(reverse("asistencia_resumen")).status_code, 200)
        self.login(ROL_TESORERO)
        self.assertEqual(self.client.get(reverse("asistencia_registrar")).status_code, 403)
        self.assertEqual(self.client.get(reverse("asistencia_historial")).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("asistencia_registrar")).status_code, 302)

    def test_guardado_transaccional_y_edicion_sin_duplicar(self):
        self.login(ROL_ADMINISTRADOR)
        datos = {"evento_id": self.evento.pk, "fecha": self.evento.fecha.isoformat(), f"presente_{self.miembro.pk}": "on"}
        response = self.client.post(reverse("asistencia_registrar"), datos)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Asistencia.objects.filter(evento=self.evento).count(), 2)
        self.assertTrue(Asistencia.objects.get(evento=self.evento, miembro=self.miembro).presente)
        self.client.post(reverse("asistencia_registrar"), {"evento_id": self.evento.pk, "fecha": self.evento.fecha.isoformat()})
        self.assertEqual(Asistencia.objects.filter(evento=self.evento).count(), 2)
        self.assertEqual(Asistencia.objects.filter(evento=self.evento, presente=True).count(), 0)

    def test_unicidad_evento_miembro(self):
        Asistencia.objects.create(evento=self.evento, miembro=self.miembro, registrado_por=self.usuarios[ROL_ADMINISTRADOR])
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Asistencia.objects.create(evento=self.evento, miembro=self.miembro, registrado_por=self.usuarios[ROL_ADMINISTRADOR])

    def test_bloquea_cancelado_y_futuro(self):
        self.login(ROL_ADMINISTRADOR)
        for evento, texto in ((self.cancelado, "cancelado"), (self.futuro, "futuro")):
            response = self.client.post(reverse("asistencia_registrar"), {"evento_id": evento.pk, "fecha": evento.fecha.isoformat()})
            self.assertRedirects(response, reverse("asistencia_registrar"))
            self.assertFalse(Asistencia.objects.filter(evento=evento).exists())
            self.assertIn(texto, "".join(str(message) for message in response.wsgi_request._messages))

    def test_coordinador_solo_ve_sus_miembros_y_eventos(self):
        ajeno = Miembro.objects.create(nombre_completo="Ajeno", fecha_ingreso=date.today())
        otro_ministerio = Ministerio.objects.create(nombre="Jóvenes", coordinador=self.usuarios[ROL_PASTOR])
        otro_ministerio.miembros.add(ajeno)
        evento_ajeno = Evento.objects.create(titulo="Evento ajeno", tipo=Evento.TIPO_RELIGIOSO, fecha=date.today(), hora="14:00", ministerio=otro_ministerio)
        self.login(ROL_COORDINADOR)
        response = self.client.get(reverse("asistencia_registrar"), {"fecha": date.today().isoformat()})
        self.assertContains(response, self.evento.titulo)
        self.assertNotContains(response, evento_ajeno.titulo)
        response = self.client.get(reverse("asistencia_registrar"), {"fecha": date.today().isoformat(), "evento": self.evento.pk})
        self.assertContains(response, self.miembro.nombre_completo)
        self.assertNotContains(response, ajeno.nombre_completo)

    def test_coordinador_no_ve_resumen_de_ministerio_ajeno(self):
        otro_ministerio = Ministerio.objects.create(nombre="Jóvenes", coordinador=self.usuarios[ROL_PASTOR])
        evento_ajeno = Evento.objects.create(
            titulo="Evento ajeno en resumen",
            tipo=Evento.TIPO_RELIGIOSO,
            fecha=date.today(),
            hora="14:00",
            ministerio=otro_ministerio,
        )
        Asistencia.objects.create(
            evento=evento_ajeno,
            miembro=self.otro,
            presente=True,
            registrado_por=self.usuarios[ROL_PASTOR],
        )
        self.login(ROL_COORDINADOR)
        response = self.client.get(
            reverse("asistencia_resumen"),
            {"fecha": date.today().isoformat(), "ministerio": otro_ministerio.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, evento_ajeno.titulo)
        self.assertEqual(response.context["resumen"]["total"], 0)

    def test_coordinador_no_ve_asistencia_ajena_en_detalle_de_miembro(self):
        otro_ministerio = Ministerio.objects.create(nombre="Jóvenes", coordinador=self.usuarios[ROL_PASTOR])
        evento_ajeno = Evento.objects.create(
            titulo="Evento ajeno en detalle",
            tipo=Evento.TIPO_RELIGIOSO,
            fecha=date.today(),
            hora="14:00",
            ministerio=otro_ministerio,
        )
        otro_ministerio.miembros.add(self.miembro)
        Asistencia.objects.create(
            evento=evento_ajeno,
            miembro=self.miembro,
            presente=True,
            registrado_por=self.usuarios[ROL_PASTOR],
        )
        self.login(ROL_COORDINADOR)
        response = self.client.get(reverse("asistencia_miembro", args=[self.miembro.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, evento_ajeno.titulo)

    def test_inactivo_conserva_registro_y_aparece_solo_lectura(self):
        Asistencia.objects.create(evento=self.evento, miembro=self.inactivo, presente=True, registrado_por=self.usuarios[ROL_ADMINISTRADOR])
        self.login(ROL_ADMINISTRADOR)
        response = self.client.get(reverse("asistencia_registrar"), {"fecha": date.today().isoformat(), "evento": self.evento.pk})
        self.assertContains(response, self.inactivo.nombre_completo)
        self.assertContains(response, "disabled")

    def test_historial_detalle_y_calendario(self):
        self.login(ROL_PASTOR)
        Asistencia.objects.create(evento=self.evento, miembro=self.miembro, presente=True, registrado_por=self.usuarios[ROL_PASTOR])
        response = self.client.get(reverse("asistencia_historial"))
        self.assertContains(response, self.evento.titulo)
        response = self.client.get(reverse("asistencia_detalle", args=[self.evento.pk]))
        self.assertContains(response, "Presentes: 1")
        calendar = self.client.get(reverse("calendario_datos"), {"start": date.today().isoformat(), "end": (date.today() + timedelta(days=1)).isoformat()})
        self.assertIsInstance(json.loads(calendar.content), list)
        self.assertEqual(self.client.get(reverse("asistencia_resumen")).status_code, 200)
        self.assertEqual(
            self.client.get(
                reverse("asistencia_miembro", args=[self.miembro.pk])
            ).status_code,
            200,
        )

    def test_fecha_futura_muestra_bloqueo(self):
        self.login(ROL_ADMINISTRADOR)
        response = self.client.get(
            reverse("asistencia_registrar"),
            {"fecha": self.futuro.fecha.isoformat()},
        )
        self.assertContains(response, "No se puede registrar asistencia de fechas futuras.")

    def test_servicios_de_periodos_y_cero(self):
        lunes, domingo = semana_de(date(2026, 10, 28))
        self.assertEqual(lunes.weekday(), 0)
        self.assertEqual((domingo - lunes).days, 6)
        inicio, fin = rango_mes(date(2026, 12, 31))
        self.assertEqual((inicio, fin), (date(2026, 12, 1), date(2026, 12, 31)))
        self.assertEqual(resumen_periodo(date(2030, 1, 1), date(2030, 1, 31))["porcentaje"], 0)
