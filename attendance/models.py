from django.db import models

from accounts.models import Usuario
from events.models import Evento
from members.models import Miembro


class Asistencia(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="asistencias")
    miembro = models.ForeignKey(Miembro, on_delete=models.PROTECT, related_name="asistencias")
    presente = models.BooleanField("presente", default=False)
    registrado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="asistencias_registradas")
    creado = models.DateTimeField("creado", auto_now_add=True)
    actualizado = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("evento", "miembro"), name="asistencia_evento_miembro_unica"),
        ]
        indexes = [
            models.Index(fields=("evento",), name="asistencia_evento_idx"),
            models.Index(fields=("miembro",), name="asistencia_miembro_idx"),
        ]
        ordering = ["miembro__nombre_completo", "miembro_id"]
        verbose_name = "asistencia"
        verbose_name_plural = "asistencias"
