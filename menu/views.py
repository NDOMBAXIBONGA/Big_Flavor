from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from .models import Produto
from .forms import ProdutoForm, ProdutoSearchForm

class ProdutoListView(ListView):
    model = Produto
    template_name = 'lista_produtos.html'
    context_object_name = 'produtos'
    paginate_by = 12
    
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

class ProdutoDetailView(DetailView):
    model = Produto
    template_name = 'detalhes_produto.html'
    context_object_name = 'produto'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Produtos relacionados (mesma categoria)
        produto = self.get_object()
        context['produtos_relacionados'] = Produto.objects.filter(
            categoria=produto.categoria
        ).exclude(pk=produto.pk)[:4]
        return context

class ProdutoCreateView(CreateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'form_produto.html'
    success_url = reverse_lazy('lista_produtos')
    
    def form_valid(self, form):
        messages.success(self.request, 'Produto criado com sucesso!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Adicionar Novo Produto'
        context['botao_texto'] = 'Criar Produto'
        return context

class ProdutoUpdateView(UpdateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'form_produto.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Produto atualizado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('detalhes_produto', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar {self.object.nome}'
        context['botao_texto'] = 'Atualizar Produto'
        return context

class ProdutoDeleteView(DeleteView):
    model = Produto
    template_name = 'confirmar_delete.html'
    success_url = reverse_lazy('lista_produtos')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Produto deletado com sucesso!')
        return super().delete(request, *args, **kwargs)

# View para alternar status do produto
def toggle_produto_status(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    
    if produto.status == 'ativo':
        produto.status = 'inativo'
        messages.success(request, f'{produto.nome} foi desativado.')
    else:
        produto.status = 'ativo'
        messages.success(request, f'{produto.nome} foi ativado.')
    
    produto.save()
    return redirect('lista_produtos')

# Funcao para associar os Produtos no Carinho
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from carinho.models import Carrinho, ItemCarrinho  # Importar modelos do carrinho
from .models import Produto

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
    
    # Produtos relacionados (mesma categoria)
    produtos_relacionados = Produto.objects.filter(
        categoria=produto.categoria,
        status='ativo'
    ).exclude(pk=produto.pk)[:4]
    
    context = {
        'produto': produto,
        'item_carrinho': item_carrinho,  # Passar o item do carrinho separadamente
        'produtos_relacionados': produtos_relacionados,
    }
    return render(request, 'detalhes_produto.html', context)