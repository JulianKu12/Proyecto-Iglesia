from datetime import date
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views import View
from django.utils import timezone
from core.permissions import RoleRequiredMixin, ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_TESORERO, ROL_COORDINADOR, puede_ver_finanzas
from institution.models import ConfiguracionIglesia
from . import services
from .exporters import excel_response, pdf_response


REPORTS = {
    "miembros": ("Reporte general de miembros", (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO), services.miembros_report),
    "asistencia": ("Asistencia por evento", (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_COORDINADOR), services.asistencia_report),
    "ministerios": ("Participación por ministerio", (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO, ROL_COORDINADOR), services.ministerios_report),
    "ingresos": ("Ingresos por periodo", (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_TESORERO), services.ingresos_report),
}


class ReportesView(RoleRequiredMixin, View):
    allowed_roles = tuple({role for _, roles, _ in REPORTS.values() for role in roles})

    def get(self, request):
        tipo = request.GET.get("tipo", "miembros")
        if tipo not in REPORTS or not request.user.groups.filter(name__in=REPORTS[tipo][1]).exists():
            raise PermissionDenied
        if tipo == "ingresos" and not puede_ver_finanzas(request.user):
            raise PermissionDenied
        params = dict(request.GET.items())
        if tipo == "ingresos":
            params.setdefault("desde", date.today().replace(day=1).isoformat())
            params.setdefault("hasta", date.today().isoformat())
        for key in ("desde", "hasta"):
            if params.get(key):
                params[key] = date.fromisoformat(params[key])
        filas, headers = REPORTS[tipo][2](params, request.user)
        keys = {"miembros": ["nombre","telefono","correo","fecha","estado","ministerios"], "asistencia":["fecha","titulo","tipo","ministerio","presentes","ausentes","total","porcentaje"], "ministerios":["ministerio","coordinador","integrantes","eventos","registros","presentes","porcentaje"], "ingresos":["fecha","concepto","metodo","miembro","monto","estado"]}[tipo]
        rows = [[fila.get(key, "") for key in keys] for fila in filas]
        if request.GET.get("export") == "excel":
            return excel_response(REPORTS[tipo][0], headers, rows, f"reporte_{tipo}_{timezone.localdate()}", str(ConfiguracionIglesia.objects.first() or "Iglesia"))
        if request.GET.get("export") == "pdf":
            return pdf_response(REPORTS[tipo][0], headers, rows, f"reporte_{tipo}_{timezone.localdate()}", str(ConfiguracionIglesia.objects.first() or "Iglesia"), request.user)
        page = Paginator(filas, 20).get_page(request.GET.get("page"))
        return render(request, "reports/lista.html", {"tipo": tipo, "titulo": REPORTS[tipo][0], "filas": page, "headers": headers, "reportes": REPORTS})
