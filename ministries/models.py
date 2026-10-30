from django.db import models
from django.db.models.functions import Lower
from django.core.exceptions import ValidationError

from accounts.models import Usuario
from members.models import Miembro


class Ministerio(models.Model):
    nombre = models.CharField("nombre", max_length=150)
    descripcion = models.TextField("descripción", blank=True)
    coordinador = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ministerios_coordinados",
        verbose_name="coordinador",
    )
    activo = models.BooleanField("activo", default=True)
    miembros = models.ManyToManyField(Miembro, blank=True, related_name="ministerios")
    creado = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        ordering = ["nombre", "id"]
        constraints = [
            models.UniqueConstraint(Lower("nombre"), name="ministerio_nombre_ci_unico"),
        ]
        verbose_name = "ministerio"
        verbose_name_plural = "ministerios"

    def __str__(self):
        return self.nombre

    def clean(self):
        if self.coordinador_id and (
            not self.coordinador.activo
            or not self.coordinador.groups.filter(name="Coordinador").exists()
        ):
            raise ValidationError({"coordinador": "El coordinador debe ser un usuario activo con rol Coordinador."})

    @property
    def integrantes_activos(self):
        return self.miembros.filter(activo=True).count()
