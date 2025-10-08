from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import Publicacao, Comentario, Categoria, Avaliacao
from .forms import ComentarioForm, AvaliacaoForm

class ListaPublicacoesView(ListView):
    model = Publicacao
    template_name = 'lista_publicacoes.html'
    context_object_name = 'publicacoes'
    paginate_by = 6
    
    def get_queryset(self):
        queryset = Publicacao.objects.filter(publicado=True)
        
        # ✅ MODIFICADO: Usando ID em vez de slug
        categoria_id = self.kwargs.get('categoria_id')
        if categoria_id:
            categoria = get_object_or_404(Categoria, id=categoria_id)
            queryset = queryset.filter(categoria=categoria)
        
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(titulo__icontains=query) |
                Q(conteudo__icontains=query) |
                Q(resumo__icontains=query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()
        context['publicacoes_populares'] = Publicacao.objects.filter(
            publicado=True
        ).order_by('-visualizacoes')[:5]
        return context

class DetalhesPublicacaoView(DetailView):
    model = Publicacao
    template_name = 'detalhes_publicacao.html'
    context_object_name = 'publicacao'
    
    def get_queryset(self):
        return Publicacao.objects.filter(publicado=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        publicacao = self.object
        
        publicacao.incrementar_visualizacao()
        
        context['comentarios'] = publicacao.comentarios.all()
        context['comentario_form'] = ComentarioForm()
        context['avaliacao_form'] = AvaliacaoForm()
        
        context['postagens_relacionadas'] = publicacao.get_postagens_relacionadas()
        
         # Estatísticas - ✅ CORRIGIDO: Remove filtro por aprovado
        context['postagens_populares'] = Publicacao.objects.filter(
            publicado=True
        ).order_by('-visualizacoes')[:5]
        
        context['postagens_recentes'] = Publicacao.objects.filter(
            publicado=True
        ).order_by('-data_publicacao')[:5]
        
        context['postagens_mais_comentadas'] = Publicacao.objects.filter(
            publicado=True
        ).annotate(
            total_coments=Count('comentarios')
        ).order_by('-total_coments')[:5]
        
        if self.request.user.is_authenticated:
            try:
                context['avaliacao_usuario'] = Avaliacao.objects.get(
                    publicacao=publicacao,
                    usuario=self.request.user
                )
            except Avaliacao.DoesNotExist:
                context['avaliacao_usuario'] = None
        
        return context

@login_required
def adicionar_comentario(request, publicacao_id):
    # ✅ MODIFICADO: Usando ID em vez de slug
    publicacao = get_object_or_404(Publicacao, id=publicacao_id, publicado=True)
    
    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.publicacao = publicacao
            comentario.autor = request.user
            comentario.save()
            
            messages.success(request, 'Comentário adicionado com sucesso! Aguarde aprovação.')
        else:
            messages.error(request, 'Erro ao adicionar comentário.')
    
    return redirect('detalhes_publicacao', pk=publicacao.id)

@login_required
def like_comentario(request, comentario_id):
    """View para curtir/descurtir comentários"""
    comentario = get_object_or_404(Comentario, id=comentario_id)
    publicacao = comentario.publicacao
    
    if comentario.likes.filter(id=request.user.id).exists():
        comentario.likes.remove(request.user)
        messages.info(request, 'Like removido do comentário!')
    else:
        comentario.likes.add(request.user)
        messages.success(request, 'Comentário curtido!')
    
    return redirect('detalhes_publicacao', pk=publicacao.id)

@login_required
def like_publicacao(request, publicacao_id):
    # ✅ MODIFICADO: Usando ID em vez de slug
    publicacao = get_object_or_404(Publicacao, id=publicacao_id, publicado=True)
    
    if publicacao.likes.filter(id=request.user.id).exists():
        publicacao.likes.remove(request.user)
        messages.info(request, 'Like removido!')
    else:
        publicacao.likes.add(request.user)
        messages.success(request, 'Publicação curtida!')
    
    return redirect('detalhes_publicacao', pk=publicacao.id)

@login_required
def adorar_publicacao(request, publicacao_id):
    # ✅ MODIFICADO: Usando ID em vez de slug
    publicacao = get_object_or_404(Publicacao, id=publicacao_id, publicado=True)
    
    if publicacao.adores.filter(id=request.user.id).exists():
        publicacao.adores.remove(request.user)
        messages.info(request, 'Adoro removido!')
    else:
        publicacao.adores.add(request.user)
        messages.success(request, 'Você adorou esta publicação!')
    
    return redirect('detalhes_publicacao', pk=publicacao.id)

@login_required
def avaliar_publicacao(request, publicacao_id):
    # ✅ MODIFICADO: Usando ID em vez de slug
    publicacao = get_object_or_404(Publicacao, id=publicacao_id, publicado=True)
    
    if request.method == 'POST':
        form = AvaliacaoForm(request.POST)
        if form.is_valid():
            avaliacao, created = Avaliacao.objects.get_or_create(
                publicacao=publicacao,
                usuario=request.user,
                defaults={'nota': form.cleaned_data['nota']}
            )
            
            if not created:
                avaliacao.nota = form.cleaned_data['nota']
                avaliacao.save()
            
            messages.success(request, f'Avaliação de {avaliacao.nota} estrelas registrada!')
        else:
            messages.error(request, 'Erro ao registrar avaliação.')
    
    return redirect('detalhes_publicacao', pk=publicacao.id)