from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


def validar_logotipo(archivo):
    if archivo.size > 2 * 1024 * 1024:
        raise ValidationError("El logotipo no puede superar 2 MB.")


class ConfiguracionIglesia(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    nombre = models.CharField("nombre de la iglesia", max_length=200)
    logotipo = models.ImageField(
        "logotipo",
        upload_to="institucion/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "gif", "webp"]), validar_logotipo],
    )
    direccion = models.TextField("dirección", blank=True)
    telefono = models.CharField("teléfono", max_length=30, blank=True)
    correo_contacto = models.EmailField("correo de contacto", blank=True)

    class Meta:
        verbose_name = "configuración de la iglesia"
        verbose_name_plural = "configuración de la iglesia"

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class HorarioReunion(models.Model):
    DIAS = (
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miércoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sábado"),
        (6, "Domingo"),
    )
    configuracion = models.ForeignKey(ConfiguracionIglesia, on_delete=models.CASCADE, related_name="horarios")
    dia_semana = models.PositiveSmallIntegerField("día de la semana", choices=DIAS)
    hora = models.TimeField("hora")
    nombre = models.CharField("nombre de la reunión", max_length=150)

    class Meta:
        ordering = ["dia_semana", "hora"]
        verbose_name = "horario de reunión"
        verbose_name_plural = "horarios de reunión"

    def __str__(self):
        return f"{self.nombre} ({self.get_dia_semana_display()})"
