from django import forms
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