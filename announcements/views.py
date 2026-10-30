from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from core.permissions import ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO, RoleRequiredMixin

from .forms import AnuncioForm
from .models import Anuncio

ROLES_GESTION = (ROL_ADMINISTRADOR, ROL_PASTOR, ROL_SECRETARIO)


class AnunciosView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        hoy = timezone.localdate()
        anuncios = Anuncio.objects.filter(fecha_publicacion__lte=hoy).filter(
            models_q_vigentes(hoy)
        )
        page = Paginator(anuncios, 10).get_page(request.GET.get("page"))
        return render(request, "announcements/anuncios.html", {"page_obj": page, "anuncios": page.object_list, "gestion": False})


def models_q_vigentes(hoy):
    from django.db.models import Q
    return Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gte=hoy)


class GestionAnunciosView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def get(self, request):
        anuncios = Anuncio.objects.all()
        estado = request.GET.get("estado", "todos")
        hoy = timezone.localdate()
        if estado == "programados":
            anuncios = anuncios.filter(fecha_publicacion__gt=hoy)
        elif estado == "vigentes":
            anuncios = anuncios.filter(fecha_publicacion__lte=hoy).filter(models_q_vigentes(hoy))
        elif estado == "vencidos":
            anuncios = anuncios.filter(vigente_hasta__lt=hoy)
        page = Paginator(anuncios, 10).get_page(request.GET.get("page"))
        return render(request, "announcements/anuncios.html", {"page_obj": page, "anuncios": page.object_list, "gestion": True, "estado": estado})


class AnuncioCreateView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def get(self, request):
        return render(request, "announcements/anuncio_form.html", {"form": AnuncioForm()})

    def post(self, request):
        form = AnuncioForm(request.POST)
        if form.is_valid():
            anuncio = form.save(commit=False)
            anuncio.autor = request.user
            anuncio.save()
            messages.success(request, "Anuncio creado correctamente.")
            return redirect("anuncios_gestion")
        return render(request, "announcements/anuncio_form.html", {"form": form})


class AnuncioUpdateView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def get(self, request, pk):
        return render(request, "announcements/anuncio_form.html", {"form": AnuncioForm(instance=get_object_or_404(Anuncio, pk=pk)), "anuncio": get_object_or_404(Anuncio, pk=pk)})

    def post(self, request, pk):
        anuncio = get_object_or_404(Anuncio, pk=pk)
        form = AnuncioForm(request.POST, instance=anuncio)
        if form.is_valid():
            form.save()
            messages.success(request, "Anuncio actualizado correctamente.")
            return redirect("anuncios_gestion")
        return render(request, "announcements/anuncio_form.html", {"form": form, "anuncio": anuncio})


class AnuncioDeleteView(RoleRequiredMixin, View):
    allowed_roles = ROLES_GESTION

    def post(self, request, pk):
        anuncio = get_object_or_404(Anuncio, pk=pk)
        anuncio.delete()
        messages.success(request, "Anuncio eliminado correctamente.")
        return redirect("anuncios_gestion")
