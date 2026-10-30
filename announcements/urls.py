from django.urls import path

from .views import AnuncioCreateView, AnuncioDeleteView, AnuncioUpdateView, AnunciosView, GestionAnunciosView

urlpatterns = [
    path("", AnunciosView.as_view(), name="anuncios"),
    path("gestionar/", GestionAnunciosView.as_view(), name="anuncios_gestion"),
    path("nuevo/", AnuncioCreateView.as_view(), name="anuncio_crear"),
    path("<int:pk>/editar/", AnuncioUpdateView.as_view(), name="anuncio_editar"),
    path("<int:pk>/eliminar/", AnuncioDeleteView.as_view(), name="anuncio_eliminar"),
]
