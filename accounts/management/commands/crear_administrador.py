from getpass import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Usuario
from core.permissions import ROL_ADMINISTRADOR


class Command(BaseCommand):
    help = "Crea el primer usuario con rol Administrador."

    def add_arguments(self, parser):
        parser.add_argument("--correo", required=True)
        parser.add_argument("--nombre", required=True)
        parser.add_argument("--contraseña")

    def handle(self, *args, **options):
        if Usuario.objects.exists():
            raise CommandError("Ya existen usuarios; no se creó otro administrador.")
        password = options["contraseña"]
        if password is None:
            password = getpass("Contraseña: ")
            confirmacion = getpass("Confirma la contraseña: ")
            if password != confirmacion:
                raise CommandError("Las contraseñas no coinciden.")
            if not password:
                raise CommandError("La contraseña no puede estar vacía.")
        try:
            validate_password(password)
        except ValidationError as error:
            raise CommandError("La contraseña no cumple los requisitos: " + " ".join(error.messages)) from error
        usuario = Usuario.objects.create_superuser(
            correo=options["correo"],
            nombre=options["nombre"],
            password=password,
        )
        from django.contrib.auth.models import Group
        usuario.groups.add(Group.objects.get(name=ROL_ADMINISTRADOR))
        self.stdout.write(self.style.SUCCESS("Administrador creado correctamente."))
