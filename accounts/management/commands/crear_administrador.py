from django.core.management.base import BaseCommand, CommandError

from accounts.models import Usuario
from core.permissions import ROL_ADMINISTRADOR


class Command(BaseCommand):
    help = "Crea el primer usuario con rol Administrador."

    def add_arguments(self, parser):
        parser.add_argument("--correo", required=True)
        parser.add_argument("--nombre", required=True)
        parser.add_argument("--contraseña", required=True)

    def handle(self, *args, **options):
        if Usuario.objects.exists():
            raise CommandError("Ya existen usuarios; no se creó otro administrador.")
        usuario = Usuario.objects.create_superuser(
            correo=options["correo"],
            nombre=options["nombre"],
            password=options["contraseña"],
        )
        from django.contrib.auth.models import Group
        usuario.groups.add(Group.objects.get(name=ROL_ADMINISTRADOR))
        self.stdout.write(self.style.SUCCESS("Administrador creado correctamente."))
