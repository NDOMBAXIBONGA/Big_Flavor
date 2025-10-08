# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import VideoHistoria
from .forms import VideoHistoriaForm

def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def upload_video_historia(request):
    if request.method == 'POST':
        form = VideoHistoriaForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save()
            messages.success(request, f'Vídeo "{video.titulo}" adicionado com sucesso!')
            return redirect('lista_videos_historia')
    else:
        form = VideoHistoriaForm()
    
    return render(request, 'upload_video_historia.html', {
        'form': form,
        'titulo_pagina': 'Adicionar Vídeo à História'
    })

@login_required
@user_passes_test(is_staff)
def lista_videos_historia(request):
    videos = VideoHistoria.objects.all().order_by('ordem_exibicao', '-data_criacao')
    return render(request, 'lista_videos_historia.html', {
        'videos': videos,
        'titulo_pagina': 'Gerenciar Vídeos da História'
    })

@login_required
@user_passes_test(is_staff)
def editar_video_historia(request, video_id):
    video = get_object_or_404(VideoHistoria, id=video_id)
    
    if request.method == 'POST':
        form = VideoHistoriaForm(request.POST, request.FILES, instance=video)
        if form.is_valid():
            form.save()
            messages.success(request, f'Vídeo "{video.titulo}" atualizado com sucesso!')
            return redirect('lista_videos_historia')
    else:
        form = VideoHistoriaForm(instance=video)
    
    return render(request, 'upload_video_historia.html', {
        'form': form,
        'video': video,
        'titulo_pagina': f'Editar Vídeo: {video.titulo}'
    })

@login_required
@user_passes_test(is_staff)
def excluir_video_historia(request, video_id):
    video = get_object_or_404(VideoHistoria, id=video_id)
    
    if request.method == 'POST':
        titulo = video.titulo
        video.delete()
        messages.success(request, f'Vídeo "{titulo}" excluído com sucesso!')
        return redirect('lista_videos_historia')
    
    return render(request, 'confirmar_exclusao_video.html', {
        'video': video,
        'titulo_pagina': 'Confirmar Exclusão'
    })

def sobre_nos(request):
    # Buscar o vídeo ativo mais recente ou com maior ordem de exibição
    video_principal = VideoHistoria.objects.filter(ativo=True).order_by('-ordem_exibicao', '-data_criacao').first()
    
    # Buscar todos os vídeos ativos para uma galeria (opcional)
    videos_galeria = VideoHistoria.objects.filter(ativo=True).exclude(id=video_principal.id if video_principal else None).order_by('ordem_exibicao')[:3]
    
    return render(request, 'about.html', {
        'video_principal': video_principal,
        'videos_galeria': videos_galeria
    })