from django import forms
from django.core.cache import cache
from .models import Produto

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            'nome', 'descricao_curta', 'descricao', 'preco', 
            'categoria', 'imagem', 'estoque', 'status'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do produto'
            }),
            'descricao_curta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição breve do produto'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descrição detalhada do produto'
            }),
            'preco': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'estoque': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'descricao_curta': 'Descrição Curta',
            'preco': 'Preço (KZ)',
        }

    def save(self, commit=True):
        # Salva o produto
        instance = super().save(commit=commit)
        
        if commit:
            # Invalidar todos os caches relacionados a produtos
            self.invalidar_cache_produtos()
        
        return instance

    def invalidar_cache_produtos(self):
        """Invalida todos os caches relacionados a produtos"""
        cache_keys_to_delete = [
            "produtos_ativos",
            "produtos_destaque",
            "produtos_recentes",
            "produtos_count",
            "categorias_produtos",
            "produtos_populares",
            f"produto_detalhe_{self.instance.id}" if hasattr(self, 'instance') and self.instance.id else None,
        ]
        
        # Adicionar caches por categoria
        categorias = Produto.objects.values_list('categoria', flat=True).distinct()
        for categoria in categorias:
            cache_keys_to_delete.extend([
                f"produtos_categoria_{categoria}",
                f"produtos_categoria_ativa_{categoria}",
            ])
        
        # Remover None values e deletar caches
        cache_keys_to_delete = [key for key in cache_keys_to_delete if key]
        for key in cache_keys_to_delete:
            cache.delete(key)

class ProdutoSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pesquisar produtos...'
        })
    )
    
    categoria = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas as Categorias')] + Produto.CATEGORIA_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    preco_min = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Preço mínimo',
            'step': '0.01'
        })
    )

    preco_max = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Preço máximo',
            'step': '0.01'
        })
    )

    ordenar = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Ordenar por'),
            ('nome', 'Nome A-Z'),
            ('-nome', 'Nome Z-A'),
            ('preco', 'Preço: Menor para Maior'),
            ('-preco', 'Preço: Maior para Menor'),
            ('-data_criacao', 'Mais Recentes'),
            ('data_criacao', 'Mais Antigos'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    def get_cache_key(self):
        """Gera uma chave de cache única baseada nos parâmetros de busca"""
        query = self.cleaned_data.get('query', '')
        categoria = self.cleaned_data.get('categoria', '')
        preco_min = self.cleaned_data.get('preco_min', '')
        preco_max = self.cleaned_data.get('preco_max', '')
        ordenar = self.cleaned_data.get('ordenar', '')
        
        cache_key = f"produtos_search_{query}_{categoria}_{preco_min}_{preco_max}_{ordenar}"
        return cache_key.replace(' ', '_').lower()