from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path('', views.ProdutoListView.as_view(), name='lista_produtos'),
    path('produto/<int:pk>/', views.ProdutoDetailView.as_view(), name='detalhes_produto'),
    path('produto/novo/', views.ProdutoCreateView.as_view(), name='criar_produto'),
    path('produto/<int:pk>/editar/', views.ProdutoUpdateView.as_view(), name='editar_produto'),
    path('produto/<int:pk>/deletar/', views.ProdutoDeleteView.as_view(), name='deletar_produto'),
    path('produto/<int:pk>/toggle-status/', views.toggle_produto_status, name='toggle_produto_status'),
    # URLs para favoritos
    path('favoritos/adicionar/<int:produto_id>/', views.adicionar_favorito, name='adicionar_favorito'),
    path('favoritos/remover/<int:produto_id>/', views.remover_favorito, name='remover_favorito'),
    path('favoritos/', views.lista_favoritos, name='lista_favoritos'),
]

# Servir arquivos de mídia durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)