# balanco/cache_utils.py
from django.core.cache import cache
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import RelatorioBalanco

def get_relatorio_balanco_cache(relatorio_id, timeout=3600):
    """
    Obtém relatório de balanço do cache ou do banco de dados
    """
    cache_key = f"relatorio_balanco_{relatorio_id}"
    relatorio = cache.get(cache_key)
    
    if relatorio is None:
        try:
            relatorio = RelatorioBalanco.objects.select_related().get(id=relatorio_id)
            cache.set(cache_key, relatorio, timeout)
        except RelatorioBalanco.DoesNotExist:
            relatorio = None
    
    return relatorio

def get_relatorios_recentes_cache(limit=10, timeout=1800):
    """
    Obtém relatórios recentes do cache
    """
    cache_key = f"relatorios_balanco_recentes_{limit}"
    relatorios = cache.get(cache_key)
    
    if relatorios is None:
        relatorios = RelatorioBalanco.objects.all().order_by('-data_criacao')[:limit]
        cache.set(cache_key, relatorios, timeout)
    
    return relatorios

def get_relatorios_count_cache(timeout=300):
    """
    Obtém contagem de relatórios do cache
    """
    cache_key = "relatorios_balanco_count"
    count = cache.get(cache_key)
    
    if count is None:
        count = RelatorioBalanco.objects.count()
        cache.set(cache_key, count, timeout)
    
    return count

def get_dashboard_estatisticas_cache(timeout=1800):
    """
    Obtém estatísticas para dashboard do cache
    """
    cache_key = "dashboard_estatisticas"
    estatisticas = cache.get(cache_key)
    
    if estatisticas is None:
        # Relatório dos últimos 30 dias
        data_fim = timezone.now().date()
        data_inicio = data_fim - timedelta(days=30)
        
        try:
            relatorio = RelatorioBalanco.objects.filter(
                data_inicio=data_inicio,
                data_fim=data_fim
            ).first()
            
            if not relatorio:
                relatorio = RelatorioBalanco.objects.create(
                    nome_relatorio="Dashboard - Últimos 30 Dias",
                    data_inicio=data_inicio,
                    data_fim=data_fim
                )
                relatorio.buscar_dados_carrinho()
            
            estatisticas = {
                'total_geral': relatorio.total_geral,
                'total_pedidos': relatorio.total_pedidos_periodo,
                'pedidos_entregues': relatorio.total_pedidos_entregues,
                'taxa_sucesso': relatorio.taxa_sucesso,
                'valor_medio_pedido': relatorio.valor_medio_pedido,
                'pedidos_por_dia': relatorio.pedidos_por_dia,
            }
            
            cache.set(cache_key, estatisticas, timeout)
            
        except Exception as e:
            print(f"Erro ao gerar estatísticas do dashboard: {e}")
            estatisticas = {}
    
    return estatisticas

def get_relatorios_por_periodo_cache(data_inicio, data_fim, timeout=3600):
    """
    Obtém relatórios por período específico do cache
    """
    cache_key = f"relatorios_periodo_{data_inicio}_{data_fim}"
    relatorios = cache.get(cache_key)
    
    if relatorios is None:
        relatorios = RelatorioBalanco.objects.filter(
            data_inicio=data_inicio,
            data_fim=data_fim
        ).order_by('-data_criacao')
        cache.set(cache_key, relatorios, timeout)
    
    return relatorios

def gerar_relatorio_com_cache(data_inicio, data_fim, nome_relatorio="Relatório Cache"):
    """
    Gera ou recupera relatório do cache
    """
    cache_key = f"relatorio_gerado_{data_inicio}_{data_fim}"
    relatorio = cache.get(cache_key)
    
    if relatorio is None:
        # Verificar se já existe relatório para este período
        relatorio_existente = RelatorioBalanco.objects.filter(
            data_inicio=data_inicio,
            data_fim=data_fim
        ).first()
        
        if relatorio_existente:
            relatorio = relatorio_existente
        else:
            # Criar novo relatório
            relatorio = RelatorioBalanco.objects.create(
                nome_relatorio=nome_relatorio,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            relatorio.buscar_dados_carrinho()
        
        cache.set(cache_key, relatorio, 7200)  # 2 horas de cache
    
    return relatorio

def invalidar_cache_balanco_completo():
    """
    Invalida todo o cache relacionado a balanços
    """
    cache_keys = [
        "dashboard_estatisticas",
        "relatorios_balanco_count",
    ]
    
    # Buscar e invalidar caches de relatórios específicos
    for key in cache.keys('*relatorio_balanco_*'):
        cache_keys.append(key)
    
    for key in cache.keys('*relatorios_balanco_*'):
        cache_keys.append(key)
    
    for key in cache.keys('*relatorio_gerado_*'):
        cache_keys.append(key)
    
    for key in set(cache_keys):  # Remover duplicatas
        cache.delete(key)

def get_estatisticas_comparativas_cache(timeout=3600):
    """
    Obtém estatísticas comparativas entre períodos
    """
    cache_key = "estatisticas_comparativas"
    estatisticas = cache.get(cache_key)
    
    if estatisticas is None:
        hoje = timezone.now().date()
        
        # Período atual (últimos 30 dias)
        periodo_atual_inicio = hoje - timedelta(days=30)
        relatorio_atual = gerar_relatorio_com_cache(periodo_atual_inicio, hoje, "Comparativo - Atual")
        
        # Período anterior (30 dias antes)
        periodo_anterior_inicio = periodo_atual_inicio - timedelta(days=30)
        periodo_anterior_fim = periodo_atual_inicio - timedelta(days=1)
        relatorio_anterior = gerar_relatorio_com_cache(periodo_anterior_inicio, periodo_anterior_fim, "Comparativo - Anterior")
        
        # Calcular variações
        variacao_total_geral = ((relatorio_atual.total_geral - relatorio_anterior.total_geral) / relatorio_anterior.total_geral * 100) if relatorio_anterior.total_geral > 0 else 0
        variacao_pedidos = ((relatorio_atual.total_pedidos_periodo - relatorio_anterior.total_pedidos_periodo) / relatorio_anterior.total_pedidos_periodo * 100) if relatorio_anterior.total_pedidos_periodo > 0 else 0
        
        estatisticas = {
            'atual': relatorio_atual,
            'anterior': relatorio_anterior,
            'variacao_total_geral': variacao_total_geral,
            'variacao_pedidos': variacao_pedidos,
            'crescimento_positivo': variacao_total_geral > 0,
        }
        
        cache.set(cache_key, estatisticas, timeout)
    
    return estatisticas