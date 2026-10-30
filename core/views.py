from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from .permissions import ROL_ADMINISTRADOR, RoleRequiredMixin


class InicioView(LoginRequiredMixin, View):
    template_name = "core/inicio.html"

    def get(self, request):
        from announcements.models import Anuncio
        from django.utils import timezone
        from events.models import Evento
        hoy = timezone.localdate()
        return render(
            request,
            self.template_name,
            {
                "proximos_eventos": Evento.objects.filter(
                    fecha__gte=hoy, estado=Evento.ESTADO_PROGRAMADO
                ).order_by("fecha", "hora")[:5],
                "avisos_importantes": Anuncio.objects.filter(
                    importante=True, fecha_publicacion__lte=hoy
                ).filter(
                    models_q_vigentes(hoy)
                )[:5],
            },
        )


class UsuariosView(RoleRequiredMixin, View):
    allowed_roles = (ROL_ADMINISTRADOR,)

    def get(self, request):
        return HttpResponse("Gestión de usuarios")


def inicio(request):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    return render(request, "core/inicio.html")


def models_q_vigentes(hoy):
    from django.db.models import Q
    return Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gte=hoy)
