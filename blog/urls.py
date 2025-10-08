from django.urls import path
from . import views


urlpatterns = [
    path('', views.ListaPublicacoesView.as_view(), name='lista_publicacoes'),
    path('categoria/<int:categoria_id>/', views.ListaPublicacoesView.as_view(), name='publicacoes_por_categoria'),
    
    # ✅ MODIFICADO: Usando ID em vez de slug
    path('publicacao/<int:pk>/', views.DetalhesPublicacaoView.as_view(), name='detalhes_publicacao'),
    
    # ✅ MODIFICADO: Usando ID em vez de slug
    path('publicacao/<int:publicacao_id>/comentar/', views.adicionar_comentario, name='adicionar_comentario'),
    path('publicacao/<int:publicacao_id>/like/', views.like_publicacao, name='like_publicacao'),
    path('publicacao/<int:publicacao_id>/adorar/', views.adorar_publicacao, name='adorar_publicacao'),
    path('publicacao/<int:publicacao_id>/avaliar/', views.avaliar_publicacao, name='avaliar_publicacao'),
    path('comentario/<int:comentario_id>/like/', views.like_comentario, name='like_comentario'),
]