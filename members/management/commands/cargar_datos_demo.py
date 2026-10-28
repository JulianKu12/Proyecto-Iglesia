from datetime import date, timedelta

from django.core.management.base import BaseCommand

from members.models import Miembro


class Command(BaseCommand):
    help = "Carga miembros ficticios para desarrollo."

    def handle(self, *args, **options):
        if Miembro.objects.exists():
            self.stdout.write(self.style.WARNING("Ya existen miembros; no se cargaron datos demo."))
            return
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
