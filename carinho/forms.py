from django import forms
from .models import ItemCarrinho, PedidoEntrega
from menu.models import Produto

class AdicionarAoCarrinhoForm(forms.ModelForm):
    quantidade = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 80px;'
        })
    )
    
    class Meta:
        model = ItemCarrinho
        fields = ['quantidade']

class PedidoEntregaForm(forms.ModelForm):
    class Meta:
        model = PedidoEntrega
        fields = ['endereco_entrega', 'observacoes']
        widgets = {
            'endereco_entrega': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Digite seu endereço completo para entrega...'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações adicionais (opcional)...'
            }),
        }
        labels = {
            'endereco_entrega': 'Endereço de Entrega',
            'observacoes': 'Observações',
        }

class AtualizarItemForm(forms.ModelForm):
    class Meta:
        model = ItemCarrinho
        fields = ['quantidade']
        widgets = {
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'style': 'width: 80px;'
            })
        }