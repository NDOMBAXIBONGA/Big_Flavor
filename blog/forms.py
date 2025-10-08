from django import forms
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