# views.py - VERSÃO CORRIGIDA
from django.shortcuts import render
from menu.models import Produto

def IndexView(request):
    # Buscar TODOS os produtos ativos das categorias desejadas em UMA consulta
    produtos = Produto.objects.filter(
        status='ativo',
        categoria__in=['hamburguer', 'pizza', 'bebida', 'sobremesa']
    ).order_by('categoria', 'nome')
    
    # Agrupar por categoria manualmente
    produtos_agrupados = {
        'hamburguer': ['hamburguer'],
        'pizza': [],
        'bebida': [],
        'sobremesa': [],
    }
    
    for produto in produtos:
        if produto.categoria in produtos_agrupados:
            produtos_agrupados[produto.categoria].append(produto)
    
    # Limitar a 4 produtos por categoria
    categorias = {
        'hamburguer': produtos_agrupados['hamburguer'][:4],
        'pizza': produtos_agrupados['pizza'][:4],
        'bebida': produtos_agrupados['bebida'][:4],
        'sobremesa': produtos_agrupados['sobremesa'][:4],
    }
    
    context = {
        'produtos_por_categoria': categorias,
    }
    return render(request, 'index.html', context)