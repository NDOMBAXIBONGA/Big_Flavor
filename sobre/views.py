# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from functools import wraps
from .models import VideoHistoria
from .forms import VideoHistoriaForm

def is_staff(user):
    return user.is_staff

# Cache decorator personalizado para vídeos
def cache_videos(timeout):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            from django.core.cache import cache
            cache_key = f"videos_{view_func.__name__}"
            response = cache.get(cache_key)
            
            if response is None:
                response = view_func(request, *args, **kwargs)
                cache.set(cache_key, response, timeout)
            
            return response
        return _wrapped_view
    return decorator

# SEM CACHE - operações de escrita (admin apenas)
@login_required
@user_passes_test(is_staff)
def upload_video_historia(request):
    if request.method == 'POST':
        form = VideoHistoriaForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save()
            
            # Invalidar cache de vídeos
            invalidar_cache_videos()
            
            messages.success(request, f'Vídeo "{video.titulo}" adicionado com sucesso!')
            return redirect('lista_videos_historia')
    else:
        form = VideoHistoriaForm()
    
    return render(request, 'upload_video_historia.html', {
        'form': form,
        'titulo_pagina': 'Adicionar Vídeo à História'
    })

# Cache para lista de vídeos (admin) - 5 minutos
@login_required
@user_passes_test(is_staff)
@cache_page(60 * 5)
@vary_on_cookie
def lista_videos_historia(request):
    videos = VideoHistoria.objects.all().order_by('ordem_exibicao', '-data_criacao')
    return render(request, 'lista_videos_historia.html', {
        'videos': videos,
        'titulo_pagina': 'Gerenciar Vídeos da História'
    })

# SEM CACHE - operações de escrita (admin apenas)
@login_required
@user_passes_test(is_staff)
def editar_video_historia(request, video_id):
    video = get_object_or_404(VideoHistoria, id=video_id)
    
    if request.method == 'POST':
        form = VideoHistoriaForm(request.POST, request.FILES, instance=video)
        if form.is_valid():
            form.save()
            
            # Invalidar cache de vídeos
            invalidar_cache_videos()
            invalidar_cache_video_especifico(video_id)
            
            messages.success(request, f'Vídeo "{video.titulo}" atualizado com sucesso!')
            return redirect('lista_videos_historia')
    else:
        form = VideoHistoriaForm(instance=video)
    
    return render(request, 'upload_video_historia.html', {
        'form': form,
        'video': video,
        'titulo_pagina': f'Editar Vídeo: {video.titulo}'
    })

# SEM CACHE - operações de escrita (admin apenas)
@login_required
@user_passes_test(is_staff)
def excluir_video_historia(request, video_id):
    video = get_object_or_404(VideoHistoria, id=video_id)
    
    if request.method == 'POST':
        titulo = video.titulo
        
        # Invalidar cache antes de deletar
        invalidar_cache_videos()
        invalidar_cache_video_especifico(video_id)
        
        video.delete()
        messages.success(request, f'Vídeo "{titulo}" excluído com sucesso!')
        return redirect('lista_videos_historia')
    
    return render(request, 'confirmar_exclusao_video.html', {
        'video': video,
        'titulo_pagina': 'Confirmar Exclusão'
    })

# Cache para página "Sobre Nós" - 1 hora (pública)
@cache_page(60 * 60)
@vary_on_cookie
def sobre_nos(request):
    # Cache para vídeo principal
    from django.core.cache import cache
    
    cache_key_principal = 'video_principal_sobre_nos'
    video_principal = cache.get(cache_key_principal)
    
    if video_principal is None:
        # Buscar o vídeo ativo mais recente ou com maior ordem de exibição
        video_principal = VideoHistoria.objects.filter(ativo=True).order_by('-ordem_exibicao', '-data_criacao').first()
        cache.set(cache_key_principal, video_principal, 60 * 60 * 2)  # 2 horas
    
    # Cache para galeria de vídeos
    cache_key_galeria = 'videos_galeria_sobre_nos'
    videos_galeria = cache.get(cache_key_galeria)
    
    if videos_galeria is None:
        # Buscar todos os vídeos ativos para uma galeria (opcional)
        videos_galeria = VideoHistoria.objects.filter(ativo=True).exclude(
            id=video_principal.id if video_principal else None
        ).order_by('ordem_exibicao')[:3]
        cache.set(cache_key_galeria, videos_galeria, 60 * 60 * 2)  # 2 horas
    
    return render(request, 'about.html', {
        'video_principal': video_principal,
        'videos_galeria': videos_galeria
    })

# API para vídeos (cache mais longo)
@cache_page(60 * 60 * 24)  # 24 horas para dados estáticos
def api_videos_historia(request):
    """API para obter vídeos da história (para AJAX)"""
    from django.core.cache import cache
    from django.http import JsonResponse
    
    cache_key = 'api_videos_historia'
    videos_data = cache.get(cache_key)
    
    if videos_data is None:
        videos = VideoHistoria.objects.filter(ativo=True).order_by('ordem_exibicao').values(
            'id', 'titulo', 'descricao', 'video_url', 'thumbnail', 'ordem_exibicao'
        )
        
        videos_data = {
            'videos': list(videos),
            'total': len(videos),
        }
        
        cache.set(cache_key, videos_data, 60 * 60 * 24)  # 24 horas
    
    return JsonResponse(videos_data)

# View para estatísticas de vídeos (admin com cache)
@login_required
@user_passes_test(is_staff)
@cache_page(60 * 30)  # 30 minutos
def estatisticas_videos(request):
    """Estatísticas de vídeos (para admin)"""
    from django.core.cache import cache
    from django.db.models import Count
    
    cache_key = 'estatisticas_videos_admin'
    estatisticas = cache.get(cache_key)
    
    if estatisticas is None:
        total_videos = VideoHistoria.objects.count()
        videos_ativos = VideoHistoria.objects.filter(ativo=True).count()
        videos_por_tipo = VideoHistoria.objects.values('tipo_video').annotate(
            total=Count('id')
        ).order_by('-total')
        
        estatisticas = {
            'total_videos': total_videos,
            'videos_ativos': videos_ativos,
            'videos_por_tipo': list(videos_por_tipo),
        }
        
        cache.set(cache_key, estatisticas, 60 * 60)  # 1 hora
    
    return render(request, 'estatisticas_videos.html', {
        'estatisticas': estatisticas,
        'titulo_pagina': 'Estatísticas de Vídeos'
    })

# Funções de invalidação de cache
def invalidar_cache_videos():
    """Invalida cache geral de vídeos"""
    from django.core.cache import cache
    cache_keys = [
        'video_principal_sobre_nos',
        'videos_galeria_sobre_nos',
        'api_videos_historia',
        'estatisticas_videos_admin',
        'videos_lista_videos_historia',
    ]
    
    for key in cache_keys:
        cache.delete(key)
    
    # Também limpa padrões
    cache.delete_many_pattern('video_*')
    cache.delete_many_pattern('*videos*')
    
    print("Cache de vídeos invalidado")

def invalidar_cache_video_especifico(video_id):
    """Invalida cache de um vídeo específico"""
    from django.core.cache import cache
    cache_keys = [
        f'video_{video_id}_details',
        f'video_{video_id}_*',
    ]
    
    for key in cache_keys:
        cache.delete(key)
    
    print(f"Cache do vídeo {video_id} invalidado")

def invalidar_todos_caches_videos():
    """Invalida todos os caches relacionados a vídeos"""
    from django.core.cache import cache
    cache.delete_many_pattern('video_*')
    cache.delete_many_pattern('*video*')
    cache.delete_many_pattern('*sobre_nos*')
    print("Todos os caches de vídeos invalidados")

# Task para limpeza periódica de cache (opcional)
def limpar_cache_videos_periodicamente():
    """Limpa cache de vídeos periodicamente"""
    invalidar_todos_caches_videos()
    print("Cache de vídeos limpo periodicamente")

# Middleware para invalidar cache automaticamente
class VideoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Invalidar cache após ações específicas em vídeos
        if request.method == 'POST' and any(path in request.path for path in ['/videos/', '/video/', '/upload/', '/editar/', '/excluir/']):
            invalidar_cache_videos()
        
        return response

# View para pré-carregar cache (admin)
@login_required
@user_passes_test(is_staff)
def preload_cache_videos(request):
    """Pré-carrega o cache de vídeos (para admin)"""
    try:
        # Forçar o carregamento do cache chamando as views
        sobre_nos(request)
        api_videos_historia(request)
        lista_videos_historia(request)
        
        messages.success(request, 'Cache de vídeos pré-carregado com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao pré-carregar cache: {str(e)}')
    
    return redirect('lista_videos_historia')