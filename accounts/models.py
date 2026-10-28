from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from members.models import Miembro


class UsuarioManager(BaseUserManager):
    def create_user(self, correo, password=None, **extra_fields):
        if not correo:
            raise ValueError("El correo es obligatorio.")
        usuario = self.model(correo=self.normalize_email(correo), **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, correo, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("activo", True)
        return self.create_user(correo, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    correo = models.EmailField("correo", unique=True)
    nombre = models.CharField("nombre", max_length=150)
    activo = models.BooleanField("activo", default=True)
    is_staff = models.BooleanField("acceso al admin", default=False)
    fecha_registro = models.DateTimeField("fecha de registro", auto_now_add=True)
    miembro = models.OneToOneField(
        Miembro,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuario",
        verbose_name="miembro vinculado",
    )

    objects = UsuarioManager()
    USERNAME_FIELD = "correo"
    REQUIRED_FIELDS = ["nombre"]

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["nombre", "correo"]

    def __str__(self):
        return f"{self.nombre} ({self.correo})"

    @property
    def is_active(self):
        return self.activo
