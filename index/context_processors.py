# context_processors.py
from carinho.models import PedidoEntrega
from sobre.models import VideoHistoria
from menu.models import Favorito
from django.utils import timezone
from datetime import timedelta

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
        
        return {
            'total_pedidos': total_pedidos,
            'total_favoritos': total_favoritos,
            'total_recompensas': total_recompensas,
            'pedidos_recentes': pedidos_recentes,
            'pedido_andamento': pedido_andamento,
        }
    return {}