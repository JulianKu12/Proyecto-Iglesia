import unicodedata

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from core.permissions import (
    ROL_ADMINISTRADOR,
    ROL_PASTOR,
    ROL_SECRETARIO,
    ROL_TESORERO,
    RoleRequiredMixin,
)

from .forms import MiembroForm
from .models import Miembro

ROLES_LECTURA = (ROL_ADMINISTRADOR, ROL_SECRETARIO, ROL_PASTOR, ROL_TESORERO)
ROLES_EDICION = (ROL_ADMINISTRADOR, ROL_SECRETARIO)


def _normalizar(texto):
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(caracter) != "Mn"
    )


class MiembrosListView(RoleRequiredMixin, View):
    allowed_roles = ROLES_LECTURA

    def get(self, request):
        estado = request.GET.get("estado", "activos")
        if estado not in {"activos", "inactivos", "todos"}:
            estado = "activos"
        queryset = Miembro.objects.all()
        if estado == "activos":
            queryset = queryset.filter(activo=True)
        elif estado == "inactivos":
            queryset = queryset.filter(activo=False)
        busqueda = request.GET.get("q", "").strip()
        miembros = list(queryset)
        if busqueda:
            termino = _normalizar(busqueda)
            miembros = [m for m in miembros if termino in _normalizar(m.nombre_completo)]
        pagina = Paginator(miembros, 10).get_page(request.GET.get("page"))
        return render(
            request,
            "members/miembros_list.html",
            {"page_obj": pagina, "miembros": pagina.object_list, "estado": estado, "busqueda": busqueda},
        )


class MiembroDetailView(RoleRequiredMixin, View):
    allowed_roles = ROLES_LECTURA

    def get(self, request, pk):
        return render(request, "members/miembro_detail.html", {"miembro": get_object_or_404(Miembro, pk=pk)})


class MiembroCreateView(RoleRequiredMixin, View):
    allowed_roles = ROLES_EDICION

    def get(self, request):
        return render(request, "members/miembro_form.html", {"form": MiembroForm()})

    def post(self, request):
        form = MiembroForm(request.POST)
        if form.is_valid():
            miembro = form.save()
            messages.success(request, "Miembro registrado correctamente.")
            return redirect("miembro_detalle", miembro.pk)
        return render(request, "members/miembro_form.html", {"form": form})


class MiembroUpdateView(RoleRequiredMixin, View):
    allowed_roles = ROLES_EDICION

    def get(self, request, pk):
        miembro = get_object_or_404(Miembro, pk=pk)
        return render(request, "members/miembro_form.html", {"form": MiembroForm(instance=miembro), "miembro": miembro})

    def post(self, request, pk):
        miembro = get_object_or_404(Miembro, pk=pk)
        form = MiembroForm(request.POST, instance=miembro)
        if form.is_valid():
            form.save()
            messages.success(request, "Miembro actualizado correctamente.")
            return redirect("miembro_detalle", miembro.pk)
        return render(request, "members/miembro_form.html", {"form": form, "miembro": miembro})


class MiembroEstadoView(RoleRequiredMixin, View):
    allowed_roles = ROLES_EDICION

    def post(self, request, pk):
        miembro = get_object_or_404(Miembro, pk=pk)
        miembro.activo = request.POST.get("accion") == "reactivar"
        miembro.save(update_fields=("activo",))
        messages.success(request, f"Miembro {'reactivado' if miembro.activo else 'desactivado'} correctamente.")
        return redirect(f"{reverse('miembros')}?estado={'activos' if miembro.activo else 'inactivos'}")
