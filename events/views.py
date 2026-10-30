from datetime import datetime

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from core.permissions import (
    ROL_ADMINISTRADOR,
    ROL_COORDINADOR,
    ROL_PASTOR,
    ROL_SECRETARIO,
    ROL_TESORERO,
    RoleRequiredMixin,
)

from .forms import CancelarEventoForm, EventoForm
from .models import Evento

ROLES_GESTION = (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO)
ROLES_LECTURA = ROLES_GESTION + (ROL_TESORERO, ROL_COORDINADOR)


def _eventos_visibles(request):
    queryset = Evento.objects.select_related("ministerio").prefetch_related("responsables")
    if request.user.groups.filter(name=ROL_COORDINADOR).exists():
        queryset = queryset.filter(ministerio__coordinador=request.user)
    return queryset


class EventosListView(RoleRequiredMixin, View):
    allowed_roles = ROLES_LECTURA

    def get(self, request):
        queryset = _eventos_visibles(request)
        busqueda = request.GET.get("q", "").strip()
        tipo = request.GET.get("tipo", "")
        estado = request.GET.get("estado", "")
        ministerio = request.GET.get("ministerio", "")
        desde = request.GET.get("desde", "")
        hasta = request.GET.get("hasta", "")
        alcance = request.GET.get("alcance", "futuros")
        if busqueda:
            queryset = queryset.filter(titulo__icontains=busqueda)
        if tipo in dict(Evento.TIPOS):
            queryset = queryset.filter(tipo=tipo)
        if estado in dict(Evento.ESTADOS):
            queryset = queryset.filter(estado=estado)
        if ministerio.isdigit():
            queryset = queryset.filter(ministerio_id=ministerio)
        if desde:
            queryset = queryset.filter(fecha__gte=desde)
        elif alcance != "todos":
            queryset = queryset.filter(fecha__gte=timezone.localdate())
        if hasta:
            queryset = queryset.filter(fecha__lte=hasta)
        pagina = Paginator(queryset, 10).get_page(request.GET.get("page"))
        from ministries.models import Ministerio
        ministerios = Ministerio.objects.filter(activo=True)
        if request.user.groups.filter(name=ROL_COORDINADOR).exists():
            ministerios = ministerios.filter(coordinador=request.user)
        return render(request, "events/eventos_list.html", {"page_obj": pagina, "eventos": pagina.object_list, "busqueda": busqueda, "tipo": tipo, "estado": estado, "ministerio": ministerio, "desde": desde, "hasta": hasta, "alcance": alcance, "ministerios": ministerios, "tipos": Evento.TIPOS})


class EventoCreateView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def get(self, request):
        return render(request, "events/evento_form.html", {"form": EventoForm()})

    def post(self, request):
        form = EventoForm(request.POST)
        if form.is_valid():
            evento = form.save()
            messages.success(request, "Evento creado correctamente.")
            return redirect("evento_detalle", evento.pk)
        return render(request, "events/evento_form.html", {"form": form})


class EventoDetailView(RoleRequiredMixin, View):
    allowed_roles = ROLES_LECTURA

    def get(self, request, pk):
        evento = get_object_or_404(_eventos_visibles(request), pk=pk)
        return render(request, "events/evento_detail.html", {"evento": evento, "puede_gestionar": request.user.groups.filter(name__in=ROLES_GESTION).exists()})


class EventoUpdateView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def get(self, request, pk):
        evento = get_object_or_404(Evento, pk=pk)
        if evento.estado == Evento.ESTADO_CANCELADO:
            messages.error(request, "Un evento cancelado no se puede editar.")
            return redirect("evento_detalle", evento.pk)
        return render(request, "events/evento_form.html", {"form": EventoForm(instance=evento), "evento": evento})

    def post(self, request, pk):
        evento = get_object_or_404(Evento, pk=pk)
        if evento.estado == Evento.ESTADO_CANCELADO:
            messages.error(request, "Un evento cancelado no se puede editar.")
            return redirect("evento_detalle", evento.pk)
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            messages.success(request, "Evento actualizado correctamente.")
            return redirect("evento_detalle", evento.pk)
        return render(request, "events/evento_form.html", {"form": form, "evento": evento})


class EventoCancelarView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def post(self, request, pk):
        evento = get_object_or_404(Evento, pk=pk)
        form = CancelarEventoForm(request.POST)
        if form.is_valid():
            evento.estado = Evento.ESTADO_CANCELADO
            evento.motivo_cancelacion = form.cleaned_data["motivo_cancelacion"]
            evento.save(update_fields=("estado", "motivo_cancelacion", "actualizado"))
            messages.success(request, "Evento cancelado correctamente.")
        return redirect("evento_detalle", evento.pk)


class EventoReactivarView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def post(self, request, pk):
        evento = get_object_or_404(Evento, pk=pk)
        evento.estado = Evento.ESTADO_PROGRAMADO
        evento.motivo_cancelacion = ""
        evento.save(update_fields=("estado", "motivo_cancelacion", "actualizado"))
        messages.success(request, "Evento reactivado correctamente.")
        return redirect("evento_detalle", evento.pk)


class CalendarioView(RoleRequiredMixin, View):
    allowed_roles = ROLES_LECTURA

    def get(self, request):
        return render(request, "events/calendario.html")


class CalendarioDatosView(RoleRequiredMixin, View):
    allowed_roles = ROLES_LECTURA

    def get(self, request):
        queryset = _eventos_visibles(request)
        inicio = request.GET.get("start")
        fin = request.GET.get("end")
        if inicio:
            queryset = queryset.filter(fecha__gte=inicio[:10])
        if fin:
            queryset = queryset.filter(fecha__lt=fin[:10])
        datos = []
        for evento in queryset:
            color = "#0d6efd" if evento.tipo == Evento.TIPO_RELIGIOSO else "#198754"
            datos.append({
                "id": evento.pk,
                "title": evento.titulo,
                "start": f"{evento.fecha.isoformat()}T{evento.hora.strftime('%H:%M:%S')}",
                "url": f"/eventos/{evento.pk}/",
                "color": "#6c757d" if evento.estado == Evento.ESTADO_CANCELADO else color,
                "classNames": ["evento-cancelado"] if evento.estado == Evento.ESTADO_CANCELADO else [],
            })
        return JsonResponse(datos, safe=False)
