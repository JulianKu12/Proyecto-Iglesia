from django import forms

from members.models import Miembro

from .models import Evento


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = (
            "titulo",
            "tipo",
            "fecha",
            "hora",
            "lugar",
            "descripcion",
            "ministerio",
            "responsables",
        )
        widgets = {
            "fecha": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "hora": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "responsables": forms.SelectMultiple(attrs={"size": 8}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsables"].queryset = Miembro.objects.filter(activo=True)


class CancelarEventoForm(forms.Form):
    motivo_cancelacion = forms.CharField(label="Motivo de cancelación", required=False, widget=forms.Textarea(attrs={"rows": 3}))
