from django import forms
from django.core.cache import cache
from .models import Comentario, Avaliacao

class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Deixe seu comentário...'
            }),
        }
        labels = {
            'texto': 'Seu Comentário'
        }

    def save(self, commit=True):
        # Salva o comentário
        instance = super().save(commit=commit)
        
        # Invalida o cache de comentários após salvar
        cache_key = f"comentarios_{instance.conteudo_id}"  # assumindo que há um relacionamento com conteúdo
        cache.delete(cache_key)
        
        return instance

class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = Avaliacao
        fields = ['nota']
        widgets = {
            'nota': forms.RadioSelect(choices=[
                (1, '1 ⭐'),
                (2, '2 ⭐⭐'),
                (3, '3 ⭐⭐⭐'),
                (4, '4 ⭐⭐⭐⭐'),
                (5, '5 ⭐⭐⭐⭐⭐'),
            ])
        }

    def save(self, commit=True):
        # Salva a avaliação
        instance = super().save(commit=commit)
        
        # Invalida o cache de avaliações após salvar
        cache_key = f"avaliacoes_{instance.conteudo_id}"  # assumindo que há um relacionamento com conteúdo
        cache.delete(cache_key)
        
        # Invalida também o cache da média de avaliações
        media_cache_key = f"media_avaliacoes_{instance.conteudo_id}"
        cache.delete(media_cache_key)
        
        return instance