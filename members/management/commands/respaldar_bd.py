import sqlite3
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crea un respaldo seguro de la base SQLite y conserva los 10 más recientes."

    def handle(self, *args, **options):
        origen = Path(settings.DATABASES["default"]["NAME"])
        if origen.suffix.lower() != ".sqlite3" or not origen.exists():
            raise CommandError("La base configurada no es un archivo SQLite existente.")
        carpeta = settings.BASE_DIR / "respaldos"
        carpeta.mkdir(exist_ok=True)
        destino = carpeta / f"db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
        with sqlite3.connect(origen) as conexion_origen, sqlite3.connect(destino) as conexion_destino:
            conexion_origen.backup(conexion_destino)
        respaldos = sorted(carpeta.glob("db_*.sqlite3"), key=lambda ruta: ruta.stat().st_mtime, reverse=True)
        for antiguo in respaldos[10:]:
            antiguo.unlink()
        self.stdout.write(self.style.SUCCESS(f"Respaldo creado: {destino.name}"))
