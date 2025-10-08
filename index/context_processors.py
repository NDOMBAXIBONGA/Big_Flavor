# context_processors.py
from sobre.models import VideoHistoria

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