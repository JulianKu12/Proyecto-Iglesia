import unicodedata

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from core.permissions import (
    ROL_ADMINISTRADOR,
    ROL_COORDINADOR,
    ROL_PASTOR,
    ROL_SECRETARIO,
    RoleRequiredMixin,
)

from .forms import AgregarIntegrantesForm, MinisterioForm
from .models import Ministerio

ROLES_GESTION = (ROL_ADMINISTRADOR, ROL_SECRETARIO)
ROLES_LECTURA = (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_COORDINADOR)


def _normalizar(texto):
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(caracter) != "Mn"
    )


def _ministerios_visibles(request):
    queryset = Ministerio.objects.select_related("coordinador").annotate(
        integrantes_activos_count=Count("miembros", filter=Q(miembros__activo=True))
    ).order_by("nombre", "id")
    if request.user.groups.filter(name=ROL_COORDINADOR).exists():
        queryset = queryset.filter(coordinador=request.user)
    return queryset


class MinisteriosListView(RoleRequiredMixin, View):
    allowed_roles = ROLES_LECTURA

    def get(self, request):
        estado = request.GET.get("estado", "activos")
        if estado not in {"activos", "inactivos", "todos"}:
            estado = "activos"
        queryset = _ministerios_visibles(request)
        if estado == "activos":
            queryset = queryset.filter(activo=True)
        elif estado == "inactivos":
            queryset = queryset.filter(activo=False)
        busqueda = request.GET.get("q", "").strip()
        if busqueda:
            queryset = [ministerio for ministerio in queryset if _normalizar(busqueda) in _normalizar(ministerio.nombre)]
        pagina = Paginator(queryset, 10).get_page(request.GET.get("page"))
        return render(
            request,
            "ministries/ministerios_list.html",
            {"page_obj": pagina, "ministerios": pagina.object_list, "estado": estado, "busqueda": busqueda},
        )


class MinisterioDetailView(RoleRequiredMixin, View):
    allowed_roles = ROLES_LECTURA

    def get(self, request, pk):
        ministerio = get_object_or_404(_ministerios_visibles(request), pk=pk)
        busqueda = request.GET.get("q", "").strip()
        integrantes = ministerio.miembros.filter(activo=True).order_by("nombre_completo", "id")
        if busqueda:
            integrantes = [miembro for miembro in integrantes if _normalizar(busqueda) in _normalizar(miembro.nombre_completo)]
        integrantes_page = Paginator(integrantes, 10).get_page(request.GET.get("page"))
        from events.models import Evento
        eventos = ministerio.eventos.filter(
            fecha__gte=timezone.localdate(),
            estado=Evento.ESTADO_PROGRAMADO,
        ).order_by("fecha", "hora")
        return render(
            request,
            "ministries/ministerio_detail.html",
            {
                "ministerio": ministerio,
                "integrantes": integrantes_page,
                "busqueda": busqueda,
                "eventos": eventos,
                "puede_gestionar": request.user.groups.filter(name__in=ROLES_GESTION).exists(),
                "form_integrantes": AgregarIntegrantesForm(ministerio=ministerio),
            },
        )


class MinisterioCreateView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def get(self, request):
        return render(request, "ministries/ministerio_form.html", {"form": MinisterioForm()})

    def post(self, request):
        form = MinisterioForm(request.POST)
        if form.is_valid():
            try:
                ministerio = form.save()
            except IntegrityError:
                form.add_error("nombre", "Ya existe un ministerio con ese nombre.")
            else:
                messages.success(request, "Ministerio creado correctamente.")
                return redirect("ministerio_detalle", ministerio.pk)
        return render(request, "ministries/ministerio_form.html", {"form": form})


class MinisterioUpdateView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def get(self, request, pk):
        ministerio = get_object_or_404(Ministerio, pk=pk)
        return render(request, "ministries/ministerio_form.html", {"form": MinisterioForm(instance=ministerio), "ministerio": ministerio})

    def post(self, request, pk):
        ministerio = get_object_or_404(Ministerio, pk=pk)
        form = MinisterioForm(request.POST, instance=ministerio)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                form.add_error("nombre", "Ya existe un ministerio con ese nombre.")
            else:
                messages.success(request, "Ministerio actualizado correctamente.")
                return redirect("ministerio_detalle", ministerio.pk)
        return render(request, "ministries/ministerio_form.html", {"form": form, "ministerio": ministerio})


class MinisterioEstadoView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def post(self, request, pk):
        ministerio = get_object_or_404(Ministerio, pk=pk)
        ministerio.activo = request.POST.get("accion") == "reactivar"
        ministerio.save(update_fields=("activo",))
        if not ministerio.activo:
            messages.warning(request, "Ministerio desactivado. Sus eventos futuros no fueron cancelados.")
        else:
            messages.success(request, "Ministerio reactivado correctamente.")
        return redirect("ministerio_detalle", ministerio.pk)


class MinisterioIntegrantesView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def post(self, request, pk):
        ministerio = get_object_or_404(Ministerio, pk=pk)
        form = AgregarIntegrantesForm(request.POST, ministerio=ministerio)
        if form.is_valid():
            ministerio.miembros.add(*form.cleaned_data["miembros"])
            messages.success(request, "Integrantes agregados correctamente.")
            return redirect("ministerio_detalle", ministerio.pk)
        return render(request, "ministries/ministerio_detail.html", {"ministerio": ministerio, "form_integrantes": form, "integrantes": ministerio.miembros.filter(activo=True), "eventos": ministerio.eventos.none(), "puede_gestionar": True})


class MinisterioQuitarIntegranteView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def post(self, request, pk, miembro_pk):
        ministerio = get_object_or_404(Ministerio, pk=pk)
        miembro = get_object_or_404(ministerio.miembros, pk=miembro_pk)
        ministerio.miembros.remove(miembro)
        messages.success(request, "Integrante retirado del ministerio.")
        return redirect("ministerio_detalle", ministerio.pk)
