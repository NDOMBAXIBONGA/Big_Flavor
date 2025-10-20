# context_processors.py
from carinho.models import PedidoEntrega
from sobre.models import VideoHistoria
from menu.models import Favorito

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
        
        return {
            'total_pedidos': total_pedidos,
            'total_favoritos': total_favoritos,
            'total_recompensas': total_recompensas,
        }
    return {}