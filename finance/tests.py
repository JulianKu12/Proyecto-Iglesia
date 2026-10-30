from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from core.permissions import ROL_ADMINISTRADOR, ROL_COORDINADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_TESORERO
from members.models import Miembro

from .models import Aportacion
from .services import resumen_mensual


class FinanzasTests(TestCase):
    def setUp(self):
        self.miembro = Miembro.objects.create(nombre_completo="Miembro Financiero", fecha_ingreso=date.today())
        self.usuarios = {}
        for rol in (ROL_ADMINISTRADOR, ROL_TESORERO, ROL_PASTOR, ROL_SECRETARIO, ROL_COORDINADOR):
            usuario = Usuario.objects.create_user(f"{rol.lower()}@finanzas.test", "secreto123", nombre=rol)
            usuario.groups.add(Group.objects.get(name=rol))
            self.usuarios[rol] = usuario

    def test_permisos_y_sin_finanzas_en_roles_no_autorizados(self):
        for rol in (ROL_ADMINISTRADOR, ROL_TESORERO, ROL_PASTOR):
            self.client.force_login(self.usuarios[rol])
            self.assertEqual(self.client.get(reverse("aportaciones")).status_code, 200)
            self.assertEqual(self.client.get(reverse("finanzas_resumen")).status_code, 200)
            self.assertEqual(self.client.get(reverse("finanzas_periodo")).status_code, 200)
        for rol in (ROL_SECRETARIO, ROL_COORDINADOR):
            self.client.force_login(self.usuarios[rol])
            self.assertEqual(self.client.get(reverse("aportaciones")).status_code, 403)
            self.assertNotContains(self.client.get(reverse("inicio")), "Finanzas")

    def test_validaciones_y_aportacion_anonima(self):
        self.client.force_login(self.usuarios[ROL_TESORERO])
        datos = {"fecha": date.today().isoformat(), "monto": "0", "concepto": "ofrenda", "metodo": "efectivo", "anonima": "on"}
        response = self.client.post(reverse("aportacion_crear"), datos)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El monto")
        datos["monto"] = "100.00"
        response = self.client.post(reverse("aportacion_crear"), datos)
        self.assertEqual(response.status_code, 302)
        aportacion = Aportacion.objects.get()
        self.assertIsNone(aportacion.miembro)
        self.assertEqual(aportacion.monto, Decimal("100.00"))

    def test_anular_obliga_motivo_y_no_cuenta(self):
        aportacion = Aportacion.objects.create(fecha=date.today(), monto=Decimal("100.00"), concepto="ofrenda", metodo="efectivo", registrado_por=self.usuarios[ROL_TESORERO], modificado_por=self.usuarios[ROL_TESORERO])
        self.client.force_login(self.usuarios[ROL_TESORERO])
        self.client.post(reverse("aportacion_anular", args=[aportacion.pk]), {"motivo_anulacion": ""})
        aportacion.refresh_from_db()
        self.assertFalse(aportacion.anulada)
        self.client.post(reverse("aportacion_anular", args=[aportacion.pk]), {"motivo_anulacion": "Duplicada"})
        aportacion.refresh_from_db()
        self.assertTrue(aportacion.anulada)
        self.assertEqual(resumen_mensual(date.today().year, date.today().month)["cantidad"], 0)
        self.assertEqual(self.client.get(reverse("aportacion_editar", args=[aportacion.pk])).status_code, 302)

    def test_resumen_mes_anterior_sin_datos_y_fecha_futura(self):
        Aportacion.objects.create(fecha=date.today(), monto=Decimal("250.50"), concepto="diezmo", metodo="transferencia", miembro=self.miembro, registrado_por=self.usuarios[ROL_TESORERO], modificado_por=self.usuarios[ROL_TESORERO])
        resumen = resumen_mensual(date.today().year, date.today().month)
        self.assertEqual(resumen["total"], Decimal("250.50"))
        self.assertIsNone(resumen["porcentaje"])
        self.client.force_login(self.usuarios[ROL_TESORERO])
        response = self.client.post(reverse("aportacion_crear"), {"fecha": (date.today() + timedelta(days=1)).isoformat(), "monto": "10", "concepto": "otro", "metodo": "otro", "miembro": self.miembro.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no puede ser futura")

    def test_roles_no_autorizados_no_ven_finanzas_en_detalle_miembro(self):
        aportacion = Aportacion.objects.create(
            fecha=date.today(),
            monto=Decimal("999.00"),
            concepto="ofrenda",
            metodo="efectivo",
            miembro=self.miembro,
            registrado_por=self.usuarios[ROL_TESORERO],
            modificado_por=self.usuarios[ROL_TESORERO],
        )
        self.assertTrue(aportacion.pk)
        for rol in (ROL_SECRETARIO, ROL_COORDINADOR):
            self.client.force_login(self.usuarios[rol])
            response = self.client.get(reverse("miembro_detalle", args=[self.miembro.pk]))
            if response.status_code == 200:
                self.assertNotContains(response, "999.00")
            else:
                self.assertEqual(response.status_code, 404)
