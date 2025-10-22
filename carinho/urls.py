from django.urls import path
from . import views


urlpatterns = [
    # ... URLs existentes ...
    path('', views.ver_carrinho, name='ver_carrinho'),
    path('carrinho/adicionar/<int:produto_id>/', views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    path('carrinho/adicionar-rapido/<int:produto_id>/', views.adicionar_ao_carrinho, name='adicionar_rapido_carrinho'),
    path('carrinho/atualizar/<int:item_id>/', views.atualizar_item_carrinho, name='atualizar_item_carrinho'),
    path('carrinho/remover/<int:item_id>/', views.remover_do_carrinho, name='remover_do_carrinho'),
    path('carrinho/limpar/', views.limpar_carrinho, name='limpar_carrinho'),
    path('carrinho/solicitar-entrega/', views.solicitar_entrega, name='solicitar_entrega'),
    path('pedidos/<int:pedido_id>/', views.detalhes_pedido, name='detalhes_pedido'),
    path('pedidos/<int:pedido_id>/cancelar/', views.cancelar_pedido, name='cancelar_pedido'),
    path('pedidos/<int:pedido_id>/refazer/', views.refazer_pedido, name='refazer_pedido'),
    path('pedidos/<int:pedido_id>/alterar-estado/', views.alterar_estado_pedido, name='alterar_estado_pedido'),
    path('pedidos/historico/', views.historico_pedidos, name='historico_pedidos'),
    path('api/atualizar-quantidade/<int:item_id>/', views.atualizar_quantidade_ajax, name='atualizar_quantidade_ajax'),
]