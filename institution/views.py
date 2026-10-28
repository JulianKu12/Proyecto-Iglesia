from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from core.permissions import ROL_ADMINISTRADOR, RoleRequiredMixin

from .forms import ConfiguracionIglesiaForm, HorarioReunionFormSet
from .models import ConfiguracionIglesia


class InstitucionUpdateView(RoleRequiredMixin, View):
    allowed_roles = (ROL_ADMINISTRADOR,)

    def get(self, request):
        configuracion, _ = ConfiguracionIglesia.objects.get_or_create(pk=1, defaults={"nombre": "Iglesia"})
        return render(
            request,
            "institution/institucion_form.html",
            {"form": ConfiguracionIglesiaForm(instance=configuracion), "horarios": HorarioReunionFormSet(instance=configuracion)},
        )

    def post(self, request):
        configuracion, _ = ConfiguracionIglesia.objects.get_or_create(pk=1, defaults={"nombre": "Iglesia"})
        form = ConfiguracionIglesiaForm(request.POST, request.FILES, instance=configuracion)
        horarios = HorarioReunionFormSet(request.POST, instance=configuracion)
        if form.is_valid() and horarios.is_valid():
            configuracion = form.save()
            horarios.instance = configuracion
            horarios.save()
            messages.success(request, "La información de la iglesia fue actualizada.")
            return redirect("institucion")
        return render(request, "institution/institucion_form.html", {"form": form, "horarios": horarios})
