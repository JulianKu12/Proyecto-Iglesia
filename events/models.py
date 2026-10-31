from django.db import models

from members.models import Miembro
from ministries.models import Ministerio


class Evento(models.Model):
    TIPO_RELIGIOSO = "religioso"
    TIPO_ADMINISTRATIVO = "administrativo"
    TIPOS = (
        (TIPO_RELIGIOSO, "Religioso"),
        (TIPO_ADMINISTRATIVO, "Administrativo"),
    )
    ESTADO_PROGRAMADO = "programado"
    ESTADO_CANCELADO = "cancelado"
    ESTADOS = (
        (ESTADO_PROGRAMADO, "Programado"),
        (ESTADO_CANCELADO, "Cancelado"),
    )
    titulo = models.CharField("título", max_length=200)
    tipo = models.CharField("tipo", max_length=20, choices=TIPOS)
    fecha = models.DateField("fecha")
    hora = models.TimeField("hora")
    lugar = models.CharField("lugar", max_length=200, blank=True)
    descripcion = models.TextField("descripción", blank=True)
    ministerio = models.ForeignKey(
        Ministerio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos",
        verbose_name="ministerio",
    )
    responsables = models.ManyToManyField(Miembro, blank=True, related_name="eventos_responsable")
    estado = models.CharField("estado", max_length=20, choices=ESTADOS, default=ESTADO_PROGRAMADO)
    motivo_cancelacion = models.TextField("motivo de cancelación", blank=True)
    creado = models.DateTimeField("creado", auto_now_add=True)
    actualizado = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["fecha", "hora", "titulo"]
        verbose_name = "evento"
        verbose_name_plural = "eventos"

    def __str__(self):
        return self.titulo
