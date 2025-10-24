from carinho.models import Carrinho, ItemCarrinho  # Importar modelos do carrinho
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_cookie
from functools import wraps
from .models import Produto, Favorito
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from .forms import ProdutoForm, ProdutoSearchForm

# Cache decorator personalizado para produtos
def cache_produtos(timeout):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            from django.core.cache import cache
            
            # Chave baseada nos parâmetros de busca e usuário
            query_params = request.GET.urlencode()
            user_id = request.user.id if request.user.is_authenticated else 'anon'
            cache_key = f"produtos_{view_func.__name__}_{user_id}_{query_params}"
            
            response = cache.get(cache_key)
            
            if response is None:
                response = view_func(request, *args, **kwargs)
                cache.set(cache_key, response, timeout)
            
            return response
        return _wrapped_view
    return decorator

# Cache para lista de produtos - 15 minutos
class ProdutoListView(ListView):
    model = Produto
    template_name = 'lista_produtos.html'
    context_object_name = 'produtos'
    paginate_by = 12
    
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_queryset(self):
        queryset = Produto.objects.all()
        
        # Filtros de pesquisa
        self.form = ProdutoSearchForm(self.request.GET)
        if self.form.is_valid():
            query = self.form.cleaned_data.get('query')
            categoria = self.form.cleaned_data.get('categoria')
            
            if query:
                queryset = queryset.filter(
                    Q(nome__icontains=query) |
                    Q(descricao__icontains=query) |
                    Q(descricao_curta__icontains=query)
                )
            
            if categoria:
                queryset = queryset.filter(categoria=categoria)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = self.form if hasattr(self, 'form') else ProdutoSearchForm()
        return context

# Cache para detalhes do produto - 30 minutos
class ProdutoDetailView(DetailView):
    model = Produto
    template_name = 'detalhes_produto.html'
    context_object_name = 'produto'
    
    @method_decorator(cache_page(60 * 30))
    @method_decorator(vary_on_cookie)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Produtos relacionados (mesma categoria)
        produto = self.get_object()
        
        # Cache para produtos relacionados
        from django.core.cache import cache
        cache_key = f"produtos_relacionados_{produto.id}"
        produtos_relacionados = cache.get(cache_key)
        
        if produtos_relacionados is None:
            produtos_relacionados = Produto.objects.filter(
                categoria=produto.categoria
            ).exclude(pk=produto.pk)[:4]
            cache.set(cache_key, produtos_relacionados, 60 * 60)  # 1 hora
        
        context['produtos_relacionados'] = produtos_relacionados
        return context

# SEM CACHE - operações de escrita
class ProdutoCreateView(CreateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'form_produto.html'
    success_url = reverse_lazy('lista_produtos')
    
    def form_valid(self, form):
        messages.success(self.request, 'Produto criado com sucesso!')
        
        # Invalidar cache de produtos
        invalidar_cache_produtos()
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Adicionar Novo Produto'
        context['botao_texto'] = 'Criar Produto'
        return context

# SEM CACHE - operações de escrita
class ProdutoUpdateView(UpdateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'form_produto.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Produto atualizado com sucesso!')
        
        # Invalidar cache do produto específico e geral
        invalidar_cache_produto_especifico(self.object.id)
        invalidar_cache_produtos()
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('detalhes_produto', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar {self.object.nome}'
        context['botao_texto'] = 'Atualizar Produto'
        return context

# SEM CACHE - operações de escrita
class ProdutoDeleteView(DeleteView):
    model = Produto
    template_name = 'confirmar_delete.html'
    success_url = reverse_lazy('lista_produtos')
    
    def delete(self, request, *args, **kwargs):
        produto_id = self.get_object().id
        
        messages.success(request, 'Produto deletado com sucesso!')
        
        # Invalidar cache antes de deletar
        invalidar_cache_produto_especifico(produto_id)
        invalidar_cache_produtos()
        
        return super().delete(request, *args, **kwargs)

# SEM CACHE - operações de escrita
def toggle_produto_status(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    
    if produto.status == 'ativo':
        produto.status = 'inativo'
        messages.success(request, f'{produto.nome} foi desativado.')
    else:
        produto.status = 'ativo'
        messages.success(request, f'{produto.nome} foi ativado.')
    
    produto.save()
    
    # Invalidar cache
    invalidar_cache_produto_especifico(produto.id)
    invalidar_cache_produtos()
    
    return redirect('lista_produtos')

# Cache para lista de produtos (versão função) - 15 minutos
@cache_page(60 * 15)
@vary_on_cookie
def lista_produtos(request):
    produtos = Produto.objects.filter(status='ativo').order_by('-data_criacao')
    
    # Verificar quais produtos estão no carrinho do usuário
    produtos_no_carrinho_ids = []
    if request.user.is_authenticated:
        carrinho = Carrinho.objects.filter(usuario=request.user, estado='aberto').first()
        if carrinho:
            produtos_no_carrinho_ids = list(carrinho.itens.values_list('produto_id', flat=True))
    
    # Adicionar informação se está no carrinho para cada produto
    for produto in produtos:
        produto.no_carrinho = produto.id in produtos_no_carrinho_ids
    
    context = {
        'produtos': produtos,
    }
    return render(request, 'lista_produtos.html', context)

# Cache para detalhes do produto (versão função) - 30 minutos
@cache_page(60 * 30)
@vary_on_cookie
def detalhes_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    
    # Verificar se o produto está no carrinho do usuário
    item_carrinho = None
    if request.user.is_authenticated:
        carrinho = Carrinho.objects.filter(usuario=request.user, estado='aberto').first()
        if carrinho:
            try:
                item_carrinho = ItemCarrinho.objects.get(carrinho=carrinho, produto=produto)
            except ItemCarrinho.DoesNotExist:
                item_carrinho = None
    
    # Cache para produtos relacionados
    from django.core.cache import cache
    cache_key = f"produtos_relacionados_{produto.id}"
    produtos_relacionados = cache.get(cache_key)
    
    if produtos_relacionados is None:
        produtos_relacionados = Produto.objects.filter(
            categoria=produto.categoria,
            status='ativo'
        ).exclude(pk=produto.pk)[:4]
        cache.set(cache_key, produtos_relacionados, 60 * 60)  # 1 hora
    
    context = {
        'produto': produto,
        'item_carrinho': item_carrinho,  # Passar o item do carrinho separadamente
        'produtos_relacionados': produtos_relacionados,
    }
    return render(request, 'detalhes_produto.html', context)

# SEM CACHE - operações de escrita
@login_required
def adicionar_favorito(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    
    # Verificar se já é favorito
    favorito, created = Favorito.objects.get_or_create(
        usuario=request.user,
        produto=produto
    )
    
    if created:
        messages.success(request, f"{produto.nome} adicionado aos favoritos!")
        # Invalidar cache de favoritos
        invalidar_cache_favoritos(request.user)
    else:
        messages.info(request, f"{produto.nome} já está nos seus favoritos!")
    
    return redirect(request.META.get('HTTP_REFERER', 'lista_produtos'))

# SEM CACHE - operações de escrita
@login_required
def remover_favorito(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    
    try:
        favorito = Favorito.objects.get(usuario=request.user, produto=produto)
        favorito.delete()
        messages.success(request, f"{produto.nome} removido dos favoritos!")
        
        # Invalidar cache de favoritos
        invalidar_cache_favoritos(request.user)
        
    except Favorito.DoesNotExist:
        messages.error(request, "Este produto não estava nos seus favoritos!")
    
    return redirect(request.META.get('HTTP_REFERER', 'lista_produtos'))

# Cache para lista de favoritos - 10 minutos
@login_required
@cache_page(60 * 10)
@vary_on_cookie
def lista_favoritos(request):
    favoritos = Favorito.objects.filter(
        usuario=request.user
    ).select_related('produto')
    
    # Usando property do model
    disponiveis_count = sum(1 for fav in favoritos if fav.produto_em_estoque)
    
    context = {
        'favoritos': favoritos,
        'total_favoritos': favoritos.count(),
        'disponiveis_count': disponiveis_count,
        'categorias_count': favoritos.values('produto__categoria').distinct().count(),
    }
    
    return render(request, 'meu_favorito.html', context)

# Funções de invalidação de cache
def invalidar_cache_produtos():
    """Invalida cache geral de produtos"""
    from django.core.cache import cache
    cache_keys = [
        'produtos_lista_produtos',
        'produtos_ProdutoListView',
    ]
    
    for key in cache_keys:
        cache.delete(key)
    
    # Também limpa padrões
    cache.delete_many_pattern('produtos_*')
    
    print("Cache de produtos invalidado")

def invalidar_cache_produto_especifico(produto_id):
    """Invalida cache de um produto específico"""
    from django.core.cache import cache
    cache_keys = [
        f'produtos_detalhes_{produto_id}',
        f'produtos_relacionados_{produto_id}',
        f'produto_{produto_id}_*',
    ]
    
    for key in cache_keys:
        cache.delete(key)
    
    print(f"Cache do produto {produto_id} invalidado")

def invalidar_cache_favoritos(usuario):
    """Invalida cache de favoritos do usuário"""
    from django.core.cache import cache
    cache_keys = [
        f'favoritos_user_{usuario.id}',
        f'lista_favoritos_user_{usuario.id}',
    ]
    
    for key in cache_keys:
        cache.delete(key)
    
    print(f"Cache de favoritos invalidado para usuário {usuario.id}")

def invalidar_todos_caches_produtos():
    """Invalida todos os caches relacionados a produtos"""
    from django.core.cache import cache
    cache.delete_many_pattern('produtos_*')
    cache.delete_many_pattern('*produto*')
    cache.delete_many_pattern('favoritos_*')
    print("Todos os caches de produtos invalidados")

# API para produtos com cache
@cache_page(60 * 5)  # 5 minutos para API
def api_produtos(request):
    """API para listagem de produtos (para AJAX)"""
    from django.core.cache import cache
    from django.http import JsonResponse
    
    cache_key = f"api_produtos_{request.GET.urlencode()}"
    produtos_data = cache.get(cache_key)
    
    if produtos_data is None:
        produtos = Produto.objects.filter(status='ativo').values(
            'id', 'nome', 'preco', 'categoria', 'imagem'
        )[:20]
        
        produtos_data = {
            'produtos': list(produtos),
            'total': len(produtos),
        }
        
        cache.set(cache_key, produtos_data, 60 * 5)
    
    return JsonResponse(produtos_data)

# View para estatísticas de produtos (com cache)
@cache_page(60 * 60)  # 1 hora
def estatisticas_produtos(request):
    """Estatísticas de produtos (para admin)"""
    from django.core.cache import cache
    from django.db.models import Count, Avg
    
    cache_key = 'estatisticas_produtos'
    estatisticas = cache.get(cache_key)
    
    if estatisticas is None:
        total_produtos = Produto.objects.count()
        produtos_ativos = Produto.objects.filter(status='ativo').count()
        produtos_por_categoria = Produto.objects.values('categoria').annotate(
            total=Count('id')
        ).order_by('-total')
        
        preco_medio = Produto.objects.filter(status='ativo').aggregate(
            avg_preco=Avg('preco')
        )['avg_preco'] or 0
        
        estatisticas = {
            'total_produtos': total_produtos,
            'produtos_ativos': produtos_ativos,
            'produtos_por_categoria': list(produtos_por_categoria),
            'preco_medio': round(preco_medio, 2),
        }
        
        cache.set(cache_key, estatisticas, 60 * 60 * 2)  # 2 horas
    
    return render(request, 'estatisticas_produtos.html', estatisticas)