from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from functools import wraps  # ✅ ADICIONE ESTA IMPORT

from .models import Publicacao, Comentario, Categoria, Avaliacao
from .forms import ComentarioForm, AvaliacaoForm

# Cache para lista de publicações - 15 minutos
@method_decorator(cache_page(60 * 15), name='dispatch')
@method_decorator(vary_on_cookie, name='dispatch')
class ListaPublicacoesView(ListView):
    model = Publicacao
    template_name = 'lista_publicacoes.html'
    context_object_name = 'publicacoes'
    paginate_by = 6
    
    def get_queryset(self):
        queryset = Publicacao.objects.filter(publicado=True)
        
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

# Cache para detalhes da publicação - 10 minutos
@method_decorator(cache_page(60 * 10), name='dispatch')
@method_decorator(vary_on_cookie, name='dispatch')
class DetalhesPublicacaoView(DetailView):
    model = Publicacao
    template_name = 'detalhes_publicacao.html'
    context_object_name = 'publicacao'
    
    def get_queryset(self):
        return Publicacao.objects.filter(publicado=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        publicacao = self.object
        
        # Incrementar visualizações - não cacheado
        publicacao.incrementar_visualizacao()
        
        context['comentarios'] = publicacao.comentarios.all()
        context['comentario_form'] = ComentarioForm()
        context['avaliacao_form'] = AvaliacaoForm()
        
        context['postagens_relacionadas'] = publicacao.get_postagens_relacionadas()
        
        # Estatísticas
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

# Views que modificam dados - SEM CACHE
@login_required
def adicionar_comentario(request, publicacao_id):
    publicacao = get_object_or_404(Publicacao, id=publicacao_id, publicado=True)
    
    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.publicacao = publicacao
            comentario.autor = request.user
            comentario.save()
            
            # Invalidar cache da página de detalhes
            from django.core.cache import cache
            cache_key = f"detalhes_publicacao_{publicacao.id}"
            cache.delete(cache_key)
            
            messages.success(request, 'Comentário adicionado com sucesso! Aguarde aprovação.')
        else:
            messages.error(request, 'Erro ao adicionar comentário.')
    
    return redirect('detalhes_publicacao', pk=publicacao.id)

@login_required
def like_comentario(request, comentario_id):
    comentario = get_object_or_404(Comentario, id=comentario_id)
    publicacao = comentario.publicacao
    
    if comentario.likes.filter(id=request.user.id).exists():
        comentario.likes.remove(request.user)
        messages.info(request, 'Like removido do comentário!')
    else:
        comentario.likes.add(request.user)
        messages.success(request, 'Comentário curtido!')
    
    # Invalidar cache
    from django.core.cache import cache
    cache_key = f"detalhes_publicacao_{publicacao.id}"
    cache.delete(cache_key)
    
    return redirect('detalhes_publicacao', pk=publicacao.id)

@login_required
def like_publicacao(request, publicacao_id):
    publicacao = get_object_or_404(Publicacao, id=publicacao_id, publicado=True)
    
    if publicacao.likes.filter(id=request.user.id).exists():
        publicacao.likes.remove(request.user)
        messages.info(request, 'Like removido!')
    else:
        publicacao.likes.add(request.user)
        messages.success(request, 'Publicação curtida!')
    
    # Invalidar cache
    from django.core.cache import cache
    cache_key = f"detalhes_publicacao_{publicacao.id}"
    cache.delete(cache_key)
    
    return redirect('detalhes_publicacao', pk=publicacao.id)

@login_required
def adorar_publicacao(request, publicacao_id):
    publicacao = get_object_or_404(Publicacao, id=publicacao_id, publicado=True)
    
    if publicacao.adores.filter(id=request.user.id).exists():
        publicacao.adores.remove(request.user)
        messages.info(request, 'Adoro removido!')
    else:
        publicacao.adores.add(request.user)
        messages.success(request, 'Você adorou esta publicação!')
    
    # Invalidar cache
    from django.core.cache import cache
    cache_key = f"detalhes_publicacao_{publicacao.id}"
    cache.delete(cache_key)
    
    return redirect('detalhes_publicacao', pk=publicacao.id)

@login_required
def avaliar_publicacao(request, publicacao_id):
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
            
            # Invalidar cache
            from django.core.cache import cache
            cache_key = f"detalhes_publicacao_{publicacao.id}"
            cache.delete(cache_key)
            
            messages.success(request, f'Avaliação de {avaliacao.nota} estrelas registrada!')
        else:
            messages.error(request, 'Erro ao registrar avaliação.')
    
    return redirect('detalhes_publicacao', pk=publicacao.id)

# ✅ CORRIGIDO: Agora com import do wraps
def cache_com_invalidacao(timeout, key_prefix):
    def decorator(view_func):
        @wraps(view_func)  # ✅ Agora funciona
        def _wrapped_view(request, *args, **kwargs):
            from django.core.cache import cache
            cache_key = f"{key_prefix}_{request.user.id if request.user.is_authenticated else 'anon'}"
            response = cache.get(cache_key)
            
            if response is None:
                response = view_func(request, *args, **kwargs)
                # Para views baseadas em função, precisamos renderizar a response
                if hasattr(response, 'render'):
                    response = response.render()
                cache.set(cache_key, response, timeout)
            
            return response
        return _wrapped_view
    return decorator

# Função para invalidar cache manualmente quando necessário
def invalidar_cache_publicacoes():
    """Invalidar todo o cache relacionado a publicações"""
    from django.core.cache import cache
    cache.delete_many([
        'lista_publicacoes',
        'categorias_publicacoes',
        'publicacoes_populares'
    ])

# Exemplo de uso do decorator personalizado (opcional)
@cache_com_invalidacao(60 * 10, 'minha_view_cache')  # 10 minutos
def minha_view_cacheada(request):
    # Sua lógica aqui
    return render(request, 'meu_template.html')