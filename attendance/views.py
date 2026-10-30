from datetime import date, timedelta

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from core.permissions import (
    ROL_ADMINISTRADOR,
    ROL_COORDINADOR,
    ROL_PASTOR,
    ROL_SECRETARIO,
    RoleRequiredMixin,
)
from events.models import Evento
from members.models import Miembro
from ministries.models import Ministerio

from .models import Asistencia
from .services import rango_mes, resumen_evento, resumen_periodo, semana_de

ROLES_ASISTENCIA = (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_COORDINADOR)
ROLES_GESTION = (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO)


def eventos_visibles(request):
    queryset = Evento.objects.select_related("ministerio")
    if request.user.groups.filter(name=ROL_COORDINADOR).exists():
        queryset = queryset.filter(ministerio__coordinador=request.user)
    return queryset


def miembros_para_evento(request, evento):
    if request.user.groups.filter(name=ROL_COORDINADOR).exists():
        return Miembro.objects.filter(activo=True, ministerios__coordinador=request.user, ministerios=evento.ministerio).distinct()
    return Miembro.objects.filter(activo=True)


def fecha_recibida(valor):
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        return timezone.localdate()


class RegistrarAsistenciaView(RoleRequiredMixin, View):
    allowed_roles = ROLES_ASISTENCIA

    def get(self, request):
        fecha = fecha_recibida(request.GET.get("fecha"))
        eventos = eventos_visibles(request).filter(fecha=fecha, estado=Evento.ESTADO_PROGRAMADO)
        evento = None
        if request.GET.get("evento") and eventos.filter(pk=request.GET["evento"]).exists():
            evento = eventos.get(pk=request.GET["evento"])
        return render(request, "attendance/registrar.html", self.context(request, fecha, eventos, evento))

    def post(self, request):
        fecha = fecha_recibida(request.POST.get("fecha"))
        evento = get_object_or_404(eventos_visibles(request), pk=request.POST.get("evento_id"))
        if evento.estado == Evento.ESTADO_CANCELADO:
            messages.error(request, "No se puede registrar asistencia de un evento cancelado.")
            return redirect("asistencia_registrar")
        if evento.fecha > timezone.localdate():
            messages.error(request, "No se puede registrar asistencia de un evento futuro.")
            return redirect("asistencia_registrar")
        miembros = list(miembros_para_evento(request, evento))
        with transaction.atomic():
            for miembro in miembros:
                Asistencia.objects.update_or_create(
                    evento=evento,
                    miembro=miembro,
                    defaults={"presente": f"presente_{miembro.pk}" in request.POST, "registrado_por": request.user},
                )
        messages.success(request, "La asistencia fue guardada correctamente.")
        return redirect(f"{reverse('asistencia_registrar')}?fecha={evento.fecha.isoformat()}&evento={evento.pk}")

    @staticmethod
    def context(request, fecha, eventos, evento):
        miembros = []
        registros = {}
        if evento:
            activos = miembros_para_evento(request, evento)
            registrados = Miembro.objects.filter(asistencias__evento=evento)
            miembros = Miembro.objects.filter(
                Q(pk__in=activos.values("pk")) | Q(pk__in=registrados.values("pk"))
            ).distinct().order_by("activo", "nombre_completo", "id")
            registros = {registro.miembro_id: registro for registro in Asistencia.objects.filter(evento=evento)}
        return {"fecha": fecha, "eventos": eventos, "evento": evento, "miembros": miembros, "registros": registros, "es_futuro": fecha > timezone.localdate()}


class HistorialAsistenciaView(RoleRequiredMixin, View):
    allowed_roles = ROLES_ASISTENCIA

    def get(self, request):
        eventos = eventos_visibles(request).filter(asistencias__isnull=False).distinct()
        q = request.GET.get("q", "").strip()
        tipo = request.GET.get("tipo", "")
        ministerio = request.GET.get("ministerio", "")
        desde = request.GET.get("desde", "")
        hasta = request.GET.get("hasta", "")
        if q:
            eventos = eventos.filter(titulo__icontains=q)
        if tipo:
            eventos = eventos.filter(tipo=tipo)
        if ministerio.isdigit():
            eventos = eventos.filter(ministerio_id=ministerio)
        if desde:
            eventos = eventos.filter(fecha__gte=desde)
        if hasta:
            eventos = eventos.filter(fecha__lte=hasta)
        eventos = eventos.order_by("-fecha", "-hora", "-pk")
        page = Paginator(eventos, 10).get_page(request.GET.get("page"))
        filas = [resumen_evento(evento) for evento in page.object_list]
        ministerios = Ministerio.objects.filter(activo=True)
        if request.user.groups.filter(name=ROL_COORDINADOR).exists():
            ministerios = ministerios.filter(coordinador=request.user)
        return render(request, "attendance/historial.html", {"page_obj": page, "filas": filas, "q": q, "tipo": tipo, "ministerio": ministerio, "desde": desde, "hasta": hasta, "ministerios": ministerios, "tipos": Evento.TIPOS})


class DetalleAsistenciaView(RoleRequiredMixin, View):
    allowed_roles = ROLES_ASISTENCIA

    def get(self, request, pk):
        evento = get_object_or_404(eventos_visibles(request), pk=pk)
        registros = Asistencia.objects.filter(evento=evento).select_related("miembro", "registrado_por")
        return render(request, "attendance/detalle.html", {"evento": evento, "resumen": resumen_evento(evento), "registros": registros, "puede_editar": request.user.groups.filter(name__in=ROLES_ASISTENCIA).exists(), "hoy": timezone.localdate()})


class ResumenAsistenciaView(RoleRequiredMixin, View):
    allowed_roles = ROLES_ASISTENCIA

    def get(self, request):
        fecha = fecha_recibida(request.GET.get("fecha"))
        periodo = request.GET.get("periodo", "semana")
        if periodo == "mes":
            inicio, fin = rango_mes(fecha)
        else:
            periodo = "semana"
            inicio, fin = semana_de(fecha)
        ministerio = request.GET.get("ministerio", "")
        tipo = request.GET.get("tipo", "")
        resumen = resumen_periodo(inicio, fin, ministerio, tipo)
        ministerios = Ministerio.objects.filter(activo=True)
        if request.user.groups.filter(name=ROL_COORDINADOR).exists():
            ministerios = ministerios.filter(coordinador=request.user)
        anterior = inicio - timedelta(days=1)
        siguiente = fin + timedelta(days=1)
        return render(request, "attendance/resumen.html", {"resumen": resumen, "inicio": inicio, "fin": fin, "fecha": fecha, "periodo": periodo, "ministerio": ministerio, "tipo": tipo, "ministerios": ministerios, "tipos": Evento.TIPOS, "anterior": anterior, "siguiente": siguiente})


class MiembroAsistenciaView(RoleRequiredMixin, View):
    allowed_roles = ROLES_ASISTENCIA

    def get(self, request, pk):
        miembro = get_object_or_404(Miembro, pk=pk)
        if request.user.groups.filter(name=ROL_COORDINADOR).exists() and not miembro.ministerios.filter(coordinador=request.user).exists():
            from django.http import Http404
            raise Http404
        registros = Asistencia.objects.filter(miembro=miembro).select_related("evento").order_by("-evento__fecha", "-evento__hora")
        total = registros.count()
        presentes = registros.filter(presente=True).count()
        return render(request, "attendance/miembro.html", {"miembro": miembro, "registros": registros[:10], "total": total, "presentes": presentes, "porcentaje": round(presentes * 100 / total, 2) if total else 0})
