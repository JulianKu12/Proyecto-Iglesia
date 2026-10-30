from datetime import date, time

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from announcements.models import Anuncio
from attendance.models import Asistencia
from events.models import Evento
from finance.models import Aportacion
from members.models import Miembro
from ministries.models import Ministerio


class AuditoriaDeRutasTests(TestCase):
    ROLES = ("Administrador", "Pastor", "Secretario", "Tesorero", "Coordinador")
    RUTAS = {
        "inicio": ROLES,
        "login": (),
        "logout": ROLES,
        "password_reset": (),
        "password_reset_done": (),
        "password_reset_confirm": (),
        "password_reset_complete": (),
        "miembros": ("Administrador", "Pastor", "Secretario", "Tesorero", "Coordinador"),
        "miembro_detalle": ("Administrador", "Pastor", "Secretario", "Tesorero", "Coordinador"),
        "ministerios": ("Administrador", "Pastor", "Secretario", "Coordinador"),
        "ministerio_detalle": ("Administrador", "Pastor", "Secretario", "Coordinador"),
        "eventos": ROLES,
        "calendario": ROLES,
        "calendario_datos": ROLES,
        "evento_detalle": ROLES,
        "asistencia_registrar": ("Administrador", "Pastor", "Secretario", "Coordinador"),
        "asistencia_historial": ("Administrador", "Pastor", "Secretario", "Coordinador"),
        "asistencia_resumen": ("Administrador", "Pastor", "Secretario", "Coordinador"),
        "asistencia_detalle": ("Administrador", "Pastor", "Secretario", "Coordinador"),
        "asistencia_miembro": ("Administrador", "Pastor", "Secretario", "Coordinador"),
        "aportaciones": ("Administrador", "Pastor", "Tesorero"),
        "finanzas_resumen": ("Administrador", "Pastor", "Tesorero"),
        "finanzas_periodo": ("Administrador", "Pastor", "Tesorero"),
        "aportacion_detalle": ("Administrador", "Pastor", "Tesorero"),
        "anuncios": ROLES,
        "anuncios_gestion": ("Administrador", "Pastor", "Secretario"),
        "reportes": ("Administrador", "Pastor", "Secretario", "Tesorero", "Coordinador"),
        "institucion": ("Administrador",),
        "usuarios": ("Administrador",),
    }

    def setUp(self):
        self.miembro = Miembro.objects.create(nombre_completo="Auditor", fecha_ingreso=date.today())
        self.ministerio = Ministerio.objects.create(nombre="Auditoría")
        self.coordinador = self._usuario("Coordinador")
        self.ministerio.coordinador = self.coordinador
        self.ministerio.save(update_fields=("coordinador",))
        self.ministerio.miembros.add(self.miembro)
        self.evento = Evento.objects.create(
            titulo="Evento de auditoría", tipo=Evento.TIPO_RELIGIOSO,
            fecha=date.today(), hora=time(10), ministerio=self.ministerio,
        )
        self.asistencia = Asistencia.objects.create(
            evento=self.evento, miembro=self.miembro,
            presente=True, registrado_por=self._usuario("Administrador"),
        )
        self.aportacion = Aportacion.objects.create(
            fecha=date.today(), monto="10.00", concepto="ofrenda", metodo="efectivo",
            registrado_por=self._usuario("Administrador"), modificado_por=self._usuario("Administrador"),
        )
        self.anuncio = Anuncio.objects.create(
            titulo="Anuncio auditoría", contenido="Texto", autor=self._usuario("Administrador"),
        )

    def _usuario(self, rol):
        usuario = Usuario.objects.create_user(f"{rol.lower()}-{Usuario.objects.count()}@test.local", "secreto123", nombre=rol)
        usuario.groups.add(Group.objects.get(name=rol))
        return usuario

    def _url(self, nombre):
        kwargs = {
            "miembro_detalle": {"pk": self.miembro.pk},
            "ministerio_detalle": {"pk": self.ministerio.pk},
            "evento_detalle": {"pk": self.evento.pk},
            "asistencia_detalle": {"pk": self.evento.pk},
            "asistencia_miembro": {"pk": self.miembro.pk},
            "aportacion_detalle": {"pk": self.aportacion.pk},
            "password_reset_confirm": {"uidb64": "x", "token": "x"},
        }
        return reverse(nombre, kwargs=kwargs.get(nombre, {}))

    def test_todas_las_rutas_estan_declaradas_y_no_devuelven_500(self):
        usuarios = {rol: (self.coordinador if rol == "Coordinador" else self._usuario(rol)) for rol in self.ROLES}
        for rol, usuario in usuarios.items():
            self.client.force_login(usuario)
            for nombre, permitidos in self.RUTAS.items():
                with self.subTest(rol=rol, ruta=nombre):
                    respuesta = self.client.get(self._url(nombre))
                    self.assertNotEqual(respuesta.status_code, 500)
                    if nombre in {"login", "password_reset", "password_reset_done", "password_reset_confirm", "password_reset_complete"}:
                        continue
                    if rol not in permitidos:
                        self.assertEqual(respuesta.status_code, 403)
                    else:
                        self.assertIn(respuesta.status_code, (200, 302, 405))
        self.client.logout()
        for nombre in self.RUTAS:
            with self.subTest(sesion="anonima", ruta=nombre):
                respuesta = self.client.get(self._url(nombre))
                self.assertNotEqual(respuesta.status_code, 500)
