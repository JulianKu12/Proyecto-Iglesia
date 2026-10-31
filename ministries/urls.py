from django.urls import path

from .views import (
    MinisterioCreateView,
    MinisterioDetailView,
    MinisterioEstadoView,
    MinisterioIntegrantesView,
    MinisterioQuitarIntegranteView,
    MinisterioUpdateView,
    MinisteriosListView,
)

urlpatterns = [
    path("", MinisteriosListView.as_view(), name="ministerios"),
    path("nuevo/", MinisterioCreateView.as_view(), name="ministerio_crear"),
    path("<int:pk>/", MinisterioDetailView.as_view(), name="ministerio_detalle"),
    path("<int:pk>/editar/", MinisterioUpdateView.as_view(), name="ministerio_editar"),
    path("<int:pk>/estado/", MinisterioEstadoView.as_view(), name="ministerio_estado"),
    path("<int:pk>/integrantes/", MinisterioIntegrantesView.as_view(), name="ministerio_integrantes"),
    path("<int:pk>/integrantes/<int:miembro_pk>/quitar/", MinisterioQuitarIntegranteView.as_view(), name="ministerio_quitar_integrante"),
]
