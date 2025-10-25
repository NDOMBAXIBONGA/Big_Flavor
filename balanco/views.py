# balanco/views.py (opcional)
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import RelatorioBalanco

def buscar_dados_relatorio(request, pk):
    """View para buscar dados via AJAX"""
    if request.method == 'POST':
        relatorio = get_object_or_404(RelatorioBalanco, pk=pk)
        relatorio.buscar_dados_carrinho()
        
        return JsonResponse({
            'success': True,
            'entregues': relatorio.total_pedidos_entregues,
            'cancelados': relatorio.total_pedidos_cancelados,
            'valor_total': float(relatorio.valor_total_entregues),
            'taxa_sucesso': relatorio.taxa_sucesso
        })