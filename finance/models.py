from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from accounts.models import Usuario
from members.models import Miembro


class Aportacion(models.Model):
    CONCEPTOS = (
        ("diezmo", "Diezmo"),
        ("ofrenda", "Ofrenda"),
        ("donacion", "Donación"),
        ("evento_especial", "Evento especial"),
        ("otro", "Otro"),
    )
    METODOS = (
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia"),
        ("deposito", "Depósito"),
        ("cheque", "Cheque"),
        ("tarjeta", "Tarjeta"),
        ("otro", "Otro"),
    )
    fecha = models.DateField("fecha")
    monto = models.DecimalField(
        "monto",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    concepto = models.CharField("concepto", max_length=30, choices=CONCEPTOS)
    descripcion = models.TextField("descripción", blank=True)
    metodo = models.CharField("método", max_length=20, choices=METODOS)
    miembro = models.ForeignKey(Miembro, null=True, blank=True, on_delete=models.PROTECT, related_name="aportaciones")
    anulada = models.BooleanField("anulada", default=False)
    motivo_anulacion = models.TextField("motivo de anulación", blank=True)
    registrado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="aportaciones_registradas")
    modificado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="aportaciones_modificadas")
    creado = models.DateTimeField("creado", auto_now_add=True)
    actualizado = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        indexes = [models.Index(fields=("fecha",)), models.Index(fields=("miembro",))]

    def clean(self):
        if self.fecha and self.fecha > timezone.localdate():
            raise ValidationError({"fecha": "La fecha no puede ser futura."})
        if self.monto is not None and (self.monto <= 0 or self.monto > Decimal("9999999.99")):
            raise ValidationError({"monto": "El monto debe estar entre $0.01 y $9,999,999.99 MXN."})
        if self.anulada and not self.motivo_anulacion.strip():
            raise ValidationError({"motivo_anulacion": "El motivo de anulación es obligatorio."})
