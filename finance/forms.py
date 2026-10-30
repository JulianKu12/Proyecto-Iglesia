from django import forms
from django.db import models
from django.utils import timezone
from decimal import Decimal

from members.models import Miembro

from .models import Aportacion


class AportacionForm(forms.ModelForm):
    anonima = forms.BooleanField(label="Aportación anónima", required=False)

    class Meta:
        model = Aportacion
        fields = ("fecha", "monto", "concepto", "descripcion", "metodo", "miembro", "anonima")
        widgets = {
            "fecha": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "monto": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Miembro.objects.filter(activo=True)
        if self.instance.pk and self.instance.miembro_id:
            queryset = Miembro.objects.filter(
                models.Q(pk=self.instance.miembro_id) | models.Q(activo=True)
            )
        self.fields["miembro"].queryset = queryset
        if self.instance.pk:
            self.initial["anonima"] = self.instance.miembro_id is None

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("fecha") and cleaned["fecha"] > timezone.localdate():
            self.add_error("fecha", "La fecha no puede ser futura.")
        if cleaned.get("monto") and cleaned["monto"] > Decimal("9999999.99"):
            self.add_error("monto", "El monto máximo es $9,999,999.99 MXN.")
        if cleaned.get("anonima"):
            cleaned["miembro"] = None
        elif not cleaned.get("miembro") and not self.instance.miembro_id:
            self.add_error("miembro", "Selecciona un miembro o marca la aportación como anónima.")
        return cleaned

    def save(self, commit=True):
        aportacion = super().save(commit=False)
        aportacion.miembro = None if self.cleaned_data.get("anonima") else self.cleaned_data.get("miembro")
        if commit:
            aportacion.save()
        return aportacion


class AnularAportacionForm(forms.Form):
    motivo_anulacion = forms.CharField(
        label="Motivo de anulación",
        required=True,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
