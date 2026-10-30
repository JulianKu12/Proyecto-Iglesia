from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from members.models import Miembro
from ministries.models import Ministerio
from events.models import Evento
from attendance.models import Asistencia


class Command(BaseCommand):
    help = "Carga miembros ficticios para desarrollo."

    def handle(self, *args, **options):
        if not Miembro.objects.exists():
            miembros = [
                Miembro(
                    nombre_completo=f"Miembro Demo {numero:02d}",
                    telefono=f"999100{numero:04d}",
                    correo=f"demo{numero:02d}@ejemplo.test",
                    fecha_ingreso=date.today() - timedelta(days=numero * 20),
                    activo=numero % 5 != 0,
                )
                for numero in range(1, 31)
            ]
            Miembro.objects.bulk_create(miembros)
            self.stdout.write(self.style.SUCCESS("Se cargaron 30 miembros demo."))
        else:
            self.stdout.write(self.style.WARNING("Ya existen miembros; se conservaron."))

        nombres = ("Música", "Jóvenes", "Niños", "Enseñanza", "Servicio")
        coordinadores = list(
            __import__("accounts.models", fromlist=["Usuario"]).Usuario.objects.filter(
                activo=True, groups__name="Coordinador"
            ).distinct()
        )
        miembros_activos = list(Miembro.objects.filter(activo=True).order_by("id"))
        ministerios = []
        for indice, nombre in enumerate(nombres):
            ministerio, _ = Ministerio.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": f"Ministerio de {nombre.lower()}"},
            )
            if coordinadores and ministerio.coordinador_id is None:
                ministerio.coordinador = coordinadores[indice % len(coordinadores)]
                ministerio.save(update_fields=("coordinador",))
            for miembro in miembros_activos[indice::5]:
                ministerio.miembros.add(miembro)
            ministerios.append(ministerio)

        hoy = timezone.localdate()
        for numero in range(1, 26):
            fecha = hoy + timedelta(days=numero - 13)
            ministerio = ministerios[numero % len(ministerios)] if numero % 2 == 0 else None
            evento, creado = Evento.objects.get_or_create(
                titulo=f"Evento Demo {numero:02d}",
                fecha=fecha,
                defaults={
                    "tipo": Evento.TIPO_RELIGIOSO if numero % 2 else Evento.TIPO_ADMINISTRATIVO,
                    "hora": "10:00",
                    "lugar": "Salón principal",
                    "descripcion": "Evento generado para pruebas.",
                    "ministerio": ministerio,
                    "estado": Evento.ESTADO_CANCELADO if numero % 7 == 0 else Evento.ESTADO_PROGRAMADO,
                    "motivo_cancelacion": "Actividad suspendida." if numero % 7 == 0 else "",
                },
            )
            if creado and miembros_activos:
                evento.responsables.add(miembros_activos[numero % len(miembros_activos)])
            if evento.fecha <= hoy and evento.estado == Evento.ESTADO_PROGRAMADO and miembros_activos:
                registrador = coordinadores[0] if coordinadores else None
                if registrador is None:
                    from accounts.models import Usuario
                    registrador = Usuario.objects.filter(activo=True).first()
                if registrador:
                    for indice, miembro in enumerate(miembros_activos):
                        Asistencia.objects.get_or_create(
                            evento=evento,
                            miembro=miembro,
                            defaults={"presente": (indice + numero) % 4 != 0, "registrado_por": registrador},
                        )
        self.stdout.write(self.style.SUCCESS("Ministerios y eventos demo listos; puede ejecutarse nuevamente sin duplicar datos."))
