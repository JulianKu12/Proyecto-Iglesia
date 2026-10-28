from django.core.validators import RegexValidator
from django.db import models


class Miembro(models.Model):
    nombre_completo = models.CharField("nombre completo", max_length=150)
    telefono = models.CharField("teléfono", max_length=30, blank=True)
    correo = models.EmailField("correo", blank=True)
    fecha_ingreso = models.DateField("fecha de ingreso")
    activo = models.BooleanField("activo", default=True)
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)

    class Meta:
        ordering = ["nombre_completo", "id"]
        verbose_name = "miembro"
        verbose_name_plural = "miembros"

    def __str__(self):
        return self.nombre_completo
