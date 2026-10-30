from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from core.permissions import ROL_ADMINISTRADOR, ROL_TESORERO, ROL_PASTOR, RoleRequiredMixin
from members.models import Miembro

from .forms import AnularAportacionForm, AportacionForm
from .models import Aportacion
from .services import mes_anterior, mes_siguiente, rango_mes, resumen_mensual, resumen_periodo

ROLES_TODOS = (ROL_ADMINISTRADOR, ROL_TESORERO, ROL_PASTOR)
ROLES_GESTION = (ROL_ADMINISTRADOR, ROL_TESORERO)


class AportacionesListView(RoleRequiredMixin, View):
    allowed_roles = ROLES_TODOS

    def get(self, request):
        queryset = Aportacion.objects.select_related("miembro", "registrado_por")
        estado = request.GET.get("estado", "vigentes")
        if estado == "vigentes":
            queryset = queryset.filter(anulada=False)
        elif estado == "anuladas":
            queryset = queryset.filter(anulada=True)
        q = request.GET.get("q", "").strip()
        concepto = request.GET.get("concepto", "")
        metodo = request.GET.get("metodo", "")
        miembro = request.GET.get("miembro", "")
        desde = request.GET.get("desde", "")
        hasta = request.GET.get("hasta", "")
        if q:
            queryset = queryset.filter(Q(descripcion__icontains=q) | Q(miembro__nombre_completo__icontains=q))
        if concepto:
            queryset = queryset.filter(concepto=concepto)
        if metodo:
            queryset = queryset.filter(metodo=metodo)
        if miembro.isdigit():
            queryset = queryset.filter(miembro_id=miembro)
        if desde:
            queryset = queryset.filter(fecha__gte=desde)
        if hasta:
            queryset = queryset.filter(fecha__lte=hasta)
        agregado = queryset.aggregate(total=Sum("monto"), cantidad=Count("id"))
        page = Paginator(queryset, 10).get_page(request.GET.get("page"))
        return render(request, "finance/aportaciones_list.html", {
            "page_obj": page, "aportaciones": page.object_list, "estado": estado, "q": q,
            "concepto": concepto, "metodo": metodo, "miembro": miembro, "desde": desde, "hasta": hasta,
            "conceptos": Aportacion.CONCEPTOS, "metodos": Aportacion.METODOS,
            "miembros": Miembro.objects.filter(activo=True), "total_filtro": agregado["total"] or Decimal("0.00"),
            "cantidad_filtro": agregado["cantidad"] or 0,
            "puede_gestionar": request.user.groups.filter(name__in=ROLES_GESTION).exists(),
        })


class AportacionCreateView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def get(self, request):
        return render(request, "finance/aportacion_form.html", {"form": AportacionForm()})

    def post(self, request):
        form = AportacionForm(request.POST)
        if form.is_valid():
            aportacion = form.save(commit=False)
            aportacion.registrado_por = request.user
            aportacion.modificado_por = request.user
            aportacion.save()
            messages.success(request, "Aportación registrada correctamente.")
            return redirect("aportacion_detalle", aportacion.pk)
        return render(request, "finance/aportacion_form.html", {"form": form})


class AportacionDetailView(RoleRequiredMixin, View):
    allowed_roles = ROLES_TODOS

    def get(self, request, pk):
        aportacion = get_object_or_404(Aportacion.objects.select_related("miembro", "registrado_por", "modificado_por"), pk=pk)
        return render(request, "finance/aportacion_detail.html", {"aportacion": aportacion, "puede_gestionar": request.user.groups.filter(name__in=ROLES_GESTION).exists()})


class AportacionUpdateView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def get(self, request, pk):
        aportacion = get_object_or_404(Aportacion, pk=pk)
        if aportacion.anulada:
            messages.error(request, "Una aportación anulada no se puede editar.")
            return redirect("aportacion_detalle", pk)
        return render(request, "finance/aportacion_form.html", {"form": AportacionForm(instance=aportacion), "aportacion": aportacion})

    def post(self, request, pk):
        aportacion = get_object_or_404(Aportacion, pk=pk)
        if aportacion.anulada:
            messages.error(request, "Una aportación anulada no se puede editar.")
            return redirect("aportacion_detalle", pk)
        form = AportacionForm(request.POST, instance=aportacion)
        if form.is_valid():
            aportacion = form.save(commit=False)
            aportacion.modificado_por = request.user
            aportacion.save()
            messages.success(request, "Aportación actualizada correctamente.")
            return redirect("aportacion_detalle", aportacion.pk)
        return render(request, "finance/aportacion_form.html", {"form": form, "aportacion": aportacion})


class AportacionAnularView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def post(self, request, pk):
        aportacion = get_object_or_404(Aportacion, pk=pk)
        form = AnularAportacionForm(request.POST)
        if form.is_valid():
            aportacion.anulada = True
            aportacion.motivo_anulacion = form.cleaned_data["motivo_anulacion"]
            aportacion.modificado_por = request.user
            aportacion.save(update_fields=("anulada", "motivo_anulacion", "modificado_por", "actualizado"))
            messages.success(request, "Aportación anulada correctamente.")
        else:
            messages.error(request, "El motivo de anulación es obligatorio.")
        return redirect("aportacion_detalle", pk)


class ResumenFinanzasView(RoleRequiredMixin, View):
    allowed_roles = ROLES_TODOS

    def get(self, request):
        hoy = timezone.localdate()
        anio = int(request.GET.get("anio", hoy.year))
        mes = int(request.GET.get("mes", hoy.month))
        resumen = resumen_mensual(anio, mes)
        anterior = mes_anterior(anio, mes)
        siguiente = mes_siguiente(anio, mes)
        return render(request, "finance/resumen.html", {"resumen": resumen, "anio": anio, "mes": mes, "meses": range(1, 13), "anterior": anterior, "siguiente": siguiente})


class IngresosPeriodoView(RoleRequiredMixin, View):
    allowed_roles = ROLES_TODOS

    def get(self, request):
        hoy = timezone.localdate()
        desde = request.GET.get("desde", hoy.replace(day=1).isoformat())
        hasta = request.GET.get("hasta", hoy.isoformat())
        try:
            inicio = date.fromisoformat(desde)
            fin = date.fromisoformat(hasta)
        except ValueError:
            inicio, fin = hoy.replace(day=1), hoy
        resumen = resumen_periodo(inicio, fin)
        return render(request, "finance/periodo.html", {"desde": inicio, "hasta": fin, "resumen": resumen})
