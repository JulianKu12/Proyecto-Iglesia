import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]
    operations = [
        migrations.CreateModel(
            name="Usuario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designa que el usuario tiene todos los permisos sin asignarlos explícitamente.", verbose_name="superuser status")),
                ("correo", models.EmailField(max_length=254, unique=True, verbose_name="correo")),
                ("nombre", models.CharField(max_length=150, verbose_name="nombre")),
                ("activo", models.BooleanField(default=True, verbose_name="activo")),
                ("is_staff", models.BooleanField(default=False, verbose_name="acceso al admin")),
                ("fecha_registro", models.DateTimeField(auto_now_add=True, verbose_name="fecha de registro")),
                ("groups", models.ManyToManyField(blank=True, help_text="Los grupos a los que pertenece este usuario. Un usuario obtiene todos los permisos concedidos a cada uno de sus grupos.", related_name="usuario_set", related_query_name="usuario", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Permisos específicos para este usuario.", related_name="usuario_set", related_query_name="usuario", to="auth.permission", verbose_name="user permissions")),
            ],
            options={"verbose_name": "usuario", "verbose_name_plural": "usuarios", "ordering": ["nombre", "correo"]},
        ),
    ]
