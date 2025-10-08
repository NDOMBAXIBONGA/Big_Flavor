# models.py
from django.db import models
from django.core.validators import FileExtensionValidator  # IMPORTAR ESTE
from django.contrib.auth.models import User

class VideoHistoria(models.Model):
    FORMATO_VIDEO_CHOICES = [
        ('mp4', 'MP4'),
        ('webm', 'WebM'),
        ('ogg', 'OGG'),
        ('youtube', 'YouTube'),
    ]
    
    titulo = models.CharField(max_length=200, verbose_name="Título do Vídeo")
    descricao = models.TextField(verbose_name="Descrição", blank=True)
    arquivo_video = models.FileField(
        upload_to='videos_historia/',
        verbose_name="Arquivo de Vídeo",
        help_text="Formatos suportados: MP4 (H.264), WebM, OGG. Tamanho máximo: 100MB",
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'webm', 'ogg'])]  # AGORA FUNCIONA
    )
    formato_video = models.CharField(
        max_length=10,
        choices=FORMATO_VIDEO_CHOICES,
        default='mp4',
        verbose_name="Formato do Vídeo"
    )
    thumbnail = models.ImageField(
        upload_to='thumbnails_videos/',
        verbose_name="Thumbnail",
        blank=True,
        null=True,
        help_text="Imagem de capa para o vídeo (16:9 recomendado)"
    )
    principal = models.BooleanField(default=False, verbose_name="Vídeo Principal")
    
    url_youtube = models.URLField(
        blank=True,
        verbose_name="URL do YouTube",
        help_text="Link alternativo do YouTube"
    )
    ativo = models.BooleanField(default=True, verbose_name="Vídeo Ativo")
    ordem_exibicao = models.IntegerField(
        default=0,
        verbose_name="Ordem de Exibição"
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Vídeo da História"
        verbose_name_plural = "Vídeos da História"
        ordering = ['ordem_exibicao', 'data_criacao']
    
    def __str__(self):
        return self.titulo
    
    def save(self, *args, **kwargs):
        # Detectar formato automaticamente
        if self.arquivo_video:
            ext = self.arquivo_video.name.split('.')[-1].lower()
            if ext in ['mp4']:
                self.formato_video = 'mp4'
            elif ext in ['webm']:
                self.formato_video = 'webm'
            elif ext in ['ogg', 'ogv']:
                self.formato_video = 'ogg'
        elif self.url_youtube:
            self.formato_video = 'youtube'
        
        super().save(*args, **kwargs)
    
    @property
    def is_youtube(self):
        return bool(self.url_youtube)
    
    def get_video_url(self):
        if self.url_youtube:
            return self.url_youtube
        elif self.arquivo_video:
            return self.arquivo_video.url
        return None
    
    def get_mime_type(self):
        mime_types = {
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'ogg': 'video/ogg'
        }
        return mime_types.get(self.formato_video, 'video/mp4')