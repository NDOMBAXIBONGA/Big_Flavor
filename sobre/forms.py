# forms.py - ATUALIZADO
from django.core.exceptions import ValidationError
import os
from .models import VideoHistoria
from django import forms
    


class VideoHistoriaForm(forms.ModelForm):
    class Meta:
        model = VideoHistoria
        fields = [
            'titulo', 
            'descricao', 
            'arquivo_video', 
            'thumbnail', 
            'url_youtube',
            'ativo',
            'ordem_exibicao'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título do vídeo...'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descrição do vídeo...'
            }),
            'arquivo_video': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/mp4,video/webm,video/ogg'
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'url_youtube': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.youtube.com/watch?v=...'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'ordem_exibicao': forms.NumberInput(attrs={
                'class': 'form-control'
            })
        }
    
    def clean_arquivo_video(self):
        arquivo = self.cleaned_data.get('arquivo_video')
        if arquivo:
            # Verificar tamanho (100MB máximo)
            if arquivo.size > 100 * 1024 * 1024:
                raise ValidationError("O arquivo de vídeo não pode exceder 100MB.")
            
            # Verificar extensão
            ext = os.path.splitext(arquivo.name)[1].lower()
            if ext not in ['.mp4', '.webm', '.ogg']:
                raise ValidationError("Formato não suportado. Use MP4, WebM ou OGG.")
            
            # Verificar se é realmente um vídeo (leitura básica do header)
            if hasattr(arquivo, 'content_type'):
                if not arquivo.content_type.startswith('video/'):
                    raise ValidationError("O arquivo deve ser um vídeo válido.")
        
        return arquivo
    
    def clean(self):
        cleaned_data = super().clean()
        arquivo_video = cleaned_data.get('arquivo_video')
        url_youtube = cleaned_data.get('url_youtube')
        
        if not arquivo_video and not url_youtube:
            raise ValidationError(
                "É necessário fornecer um arquivo de vídeo ou uma URL do YouTube."
            )
        
        return cleaned_data