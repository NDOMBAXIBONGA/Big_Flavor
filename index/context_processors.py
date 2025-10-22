import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from carinho.models import PedidoEntrega, ItemCarrinho
from menu.models import Produto, Favorito
# context_processors.py
from sobre.models import VideoHistoria
from datetime import timedelta
from decimal import Decimal

def videos_context(request):
    # Vídeo principal marcado como principal=True
    video_principal = VideoHistoria.objects.filter(
        ativo=True, 
        principal=True
    ).first()
    
    # Se não houver vídeo principal, use o primeiro por ordem
    if not video_principal:
        video_principal = VideoHistoria.objects.filter(ativo=True).first()
    
    # Vídeos para galeria
    videos_galeria = VideoHistoria.objects.filter(
        ativo=True
    ).exclude(id=video_principal.id if video_principal else None).order_by('ordem_exibicao')[:6]
    
    return {
        'video_principal': video_principal,
        'videos_galeria': videos_galeria,
    }

def dashboard_stats(request):
    if request.user.is_authenticated:
        # Total de pedidos
        total_pedidos = PedidoEntrega.objects.filter(
            carrinho__usuario=request.user
        ).count()
        
        # Total de favoritos
        total_favoritos = Favorito.objects.filter(
            usuario=request.user
        ).count()

        # PEDIDOS ENTREGUES
        pedidos_entregues = PedidoEntrega.objects.filter(
            carrinho__usuario=request.user,
            estado='entregue'
        ).count()
        
        # TOTAL GASTO - Correção aqui
        pedidos_entregues_queryset = PedidoEntrega.objects.filter(
            carrinho__usuario=request.user,
            estado='entregue'
        ).select_related('carrinho').prefetch_related('carrinho__itens__produto')

        # Calcular total gasto manualmente
        total_gasto = Decimal('0.00')
        for pedido in pedidos_entregues_queryset:
            total_gasto += pedido.carrinho.total 
        
        # Recompensas (exemplo - você pode ajustar a lógica)
        total_recompensas = 3  # Ou sua lógica específica

         # PEDIDO EM ANDAMENTO MAIS RECENTE
        pedido_andamento = PedidoEntrega.objects.filter(
            carrinho__usuario=request.user,
            estado__in=['pendente', 'confirmado', 'preparacao', 'despachado']
        ).select_related('carrinho').prefetch_related('carrinho__itens__produto').order_by('-data_solicitacao').first()
        
        # PEDIDOS RECENTES FINALIZADOS (excluindo o em andamento)
        pedidos_recentes = PedidoEntrega.objects.filter(
            carrinho__usuario=request.user,
            data_solicitacao__gte=timezone.now() - timedelta(days=30)
        ).exclude(estado__in=['pendente', 'confirmado', 'preparacao', 'despachado']).select_related('carrinho').prefetch_related('carrinho__itens__produto').order_by('-data_solicitacao')[:3]
        
        # Produtos recomendados (aleatórios a cada 24h)
        produtos_recomendados = obter_produtos_recomendados(request.user)

        return {
            'total_pedidos': total_pedidos,
            'total_favoritos': total_favoritos,
            'total_recompensas': total_recompensas,
            'pedidos_recentes': pedidos_recentes,
            'pedido_andamento': pedido_andamento,
            'pedidos_entregues': pedidos_entregues,
            'produtos_recomendados': produtos_recomendados,
            'total_gasto': total_gasto,
        }
    return {}

def obter_produtos_recomendados(usuario):
    """
    Retorna 3 produtos recomendados, mudando a cada 24h
    """
    cache_key = f"produtos_recomendados_{usuario.id}"
    produtos_recomendados = cache.get(cache_key)
    
    if produtos_recomendados is None:
        # Gera novos produtos recomendados
        produtos_recomendados = gerar_produtos_recomendados(usuario)
        
        # Cache por 24 horas
        cache.set(cache_key, produtos_recomendados, 60)
    
    return produtos_recomendados

def gerar_produtos_recomendados(usuario):
    """
    Gera produtos recomendados baseado no histórico e preferências
    """
    try:
        # Produtos disponíveis em estoque
        produtos_disponiveis = Produto.objects.filter(estoque=True)
        
        if not produtos_disponiveis.exists():
            return []
        
        # Tentativa 1: Baseado no histórico de pedidos do usuário
        produtos_historicos = obter_produtos_do_historico(usuario)
        
        # Tentativa 2: Produtos populares (mais vendidos)
        produtos_populares = obter_produtos_populares()
        
        # Tentativa 3: Produtos da mesma categoria dos favoritos
        produtos_categoria_favoritos = obter_produtos_por_categoria_favoritos(usuario)
        
        # Combinar todas as fontes
        candidatos = list(produtos_historicos) + list(produtos_populares) + list(produtos_categoria_favoritos)
        
        # Se não há candidatos suficientes, pega produtos aleatórios
        if len(candidatos) < 3:
            produtos_aleatorios = list(produtos_disponiveis.order_by('?')[:3])
            return produtos_aleatorios
        
        # Remove duplicatas e pega 3 produtos
        candidatos_unicos = list({produto.id: produto for produto in candidatos}.values())
        
        if len(candidatos_unicos) >= 3:
            return random.sample(candidatos_unicos, 3)
        else:
            # Completa com produtos aleatórios se necessário
            produtos_faltantes = 3 - len(candidatos_unicos)
            produtos_adicionais = list(produtos_disponiveis.exclude(
                id__in=[p.id for p in candidatos_unicos]
            ).order_by('?')[:produtos_faltantes])
            
            return candidatos_unicos + produtos_adicionais
            
    except Exception as e:
        print(f"Erro ao gerar recomendações: {e}")
        # Fallback: produtos aleatórios
        return list(Produto.objects.filter(estoque=True).order_by('?')[:3])

def obter_produtos_do_historico(usuario):
    """
    Obtém produtos baseados no histórico de pedidos do usuário
    """
    try:
        # Últimos 30 dias
        data_limite = timezone.now() - timedelta(days=30)
        
        # Produtos dos pedidos recentes do usuário
        produtos_ids = ItemCarrinho.objects.filter(
            carrinho__pedido_entrega__carrinho__usuario=usuario,
            carrinho__pedido_entrega__data_solicitacao__gte=data_limite
        ).values_list('produto_id', flat=True).distinct()
        
        produtos = Produto.objects.filter(
            id__in=produtos_ids,
            estoque=True
        )[:6]  # Limita a 6 produtos
        
        return produtos
        
    except Exception as e:
        print(f"Erro ao obter histórico: {e}")
        return Produto.objects.none()

def obter_produtos_populares():
    """
    Obtém produtos populares (mais vendidos)
    """
    try:
        # Produtos mais vendidos (baseado em itens de carrinho em pedidos finalizados)
        from django.db.models import Count
        
        produtos_populares_ids = ItemCarrinho.objects.filter(
            carrinho__pedido_entrega__estado='entregue'
        ).values('produto').annotate(
            total_vendido=Count('id')
        ).order_by('-total_vendido')[:6].values_list('produto', flat=True)
        
        produtos = Produto.objects.filter(
            id__in=produtos_populares_ids,
            estoque=True
        )
        
        return produtos
        
    except Exception as e:
        print(f"Erro ao obter produtos populares: {e}")
        return Produto.objects.none()

def obter_produtos_por_categoria_favoritos(usuario):
    """
    Obtém produtos da mesma categoria dos favoritos do usuário
    """
    try:
        # Categorias dos produtos favoritos do usuário
        categorias_favoritas = Favorito.objects.filter(
            usuario=usuario
        ).values_list('produto__categoria', flat=True).distinct()
        
        if categorias_favoritas:
            produtos = Produto.objects.filter(
                categoria__in=categorias_favoritas,
                estoque=True
            ).exclude(
                favorito__usuario=usuario  # Exclui produtos já favoritados
            )[:6]
            
            return produtos
        
        return Produto.objects.none()
        
    except Exception as e:
        print(f"Erro ao obter produtos por categoria: {e}")
        return Produto.objects.none()