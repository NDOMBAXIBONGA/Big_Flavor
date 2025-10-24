from django import forms
from django.core.cache import cache
from .models import ItemCarrinho, PedidoEntrega

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

    def save(self, commit=True):
        # Salva o item no carrinho
        instance = super().save(commit=commit)
        
        if commit and instance.usuario:
            # Invalida o cache do carrinho após adicionar item
            cache_key = f"carrinho_{instance.usuario.id}"
            cache.delete(cache_key)
            
            # Invalida cache do total do carrinho
            total_cache_key = f"carrinho_total_{instance.usuario.id}"
            cache.delete(total_cache_key)
        
        return instance

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

    def save(self, commit=True):
        # Salva o pedido de entrega
        instance = super().save(commit=commit)
        
        if commit and instance.pedido and instance.pedido.usuario:
            # Invalida cache de pedidos do usuário
            cache_key = f"pedidos_{instance.pedido.usuario.id}"
            cache.delete(cache_key)
            
            # Invalida cache específico do pedido
            pedido_cache_key = f"pedido_{instance.pedido.id}"
            cache.delete(pedido_cache_key)
        
        return instance

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

    def save(self, commit=True):
        # Atualiza o item do carrinho
        instance = super().save(commit=commit)
        
        if commit and instance.usuario:
            # Invalida o cache do carrinho após atualizar item
            cache_key = f"carrinho_{instance.usuario.id}"
            cache.delete(cache_key)
            
            # Invalida cache do total do carrinho
            total_cache_key = f"carrinho_total_{instance.usuario.id}"
            cache.delete(total_cache_key)
            
            # Invalida cache de itens específicos se necessário
            item_cache_key = f"carrinho_item_{instance.id}"
            cache.delete(item_cache_key)
        
        return instance