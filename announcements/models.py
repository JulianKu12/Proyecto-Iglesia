from django.db import models
from django.utils import timezone

from accounts.models import Usuario


class Anuncio(models.Model):
    titulo = models.CharField("título", max_length=200)
    contenido = models.TextField("contenido")
    fecha_publicacion = models.DateField("fecha de publicación", default=timezone.localdate)
    vigente_hasta = models.DateField("vigente hasta", null=True, blank=True)
    importante = models.BooleanField("importante", default=False)
    autor = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="anuncios")
    creado = models.DateTimeField("creado", auto_now_add=True)
    actualizado = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["-importante", "-fecha_publicacion", "-id"]

    @property
    def publicado(self):
        return self.fecha_publicacion <= timezone.localdate()

    @property
    def vigente(self):
        return self.vigente_hasta is None or self.vigente_hasta >= timezone.localdate()
