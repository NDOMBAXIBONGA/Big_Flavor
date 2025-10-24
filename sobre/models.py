# models.py
from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

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
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'webm', 'ogg'])]
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
    
    @classmethod
    def obter_videos_ativos(cls):
        """Obtém vídeos ativos com cache"""
        cache_key = 'videos_historia_ativos'
        videos = cache.get(cache_key)
        
        if videos is None:
            videos = list(cls.objects.filter(ativo=True).order_by('ordem_exibicao', 'data_criacao'))
            cache.set(cache_key, videos, 3600)  # Cache por 1 hora
        
        return videos
    
    @classmethod
    def obter_video_principal(cls):
        """Obtém vídeo principal com cache"""
        cache_key = 'video_historia_principal'
        video = cache.get(cache_key)
        
        if video is None:
            try:
                video = cls.objects.get(principal=True, ativo=True)
                cache.set(cache_key, video, 3600)  # Cache por 1 hora
            except (cls.DoesNotExist, cls.MultipleObjectsReturned):
                # Se não encontrar ou encontrar múltiplos, pega o primeiro ativo
                videos_ativos = cls.obter_videos_ativos()
                video = videos_ativos[0] if videos_ativos else None
                if video:
                    cache.set(cache_key, video, 3600)
                else:
                    cache.set(cache_key, None, 300)  # Cache negativo por 5 minutos
        
        return video
    
    @classmethod
    def obter_videos_por_formato(cls, formato):
        """Obtém vídeos por formato com cache"""
        cache_key = f'videos_historia_formato_{formato}'
        videos = cache.get(cache_key)
        
        if videos is None:
            videos = list(cls.objects.filter(
                formato_video=formato, 
                ativo=True
            ).order_by('ordem_exibicao'))
            cache.set(cache_key, videos, 3600)  # Cache por 1 hora
        
        return videos
    
    @classmethod
    def obter_videos_recentes(cls, limite=5):
        """Obtém vídeos recentes com cache"""
        cache_key = f'videos_historia_recentes_{limite}'
        videos = cache.get(cache_key)
        
        if videos is None:
            videos = list(cls.objects.filter(ativo=True).order_by('-data_criacao')[:limite])
            cache.set(cache_key, videos, 1800)  # Cache por 30 minutos
        
        return videos
    
    @classmethod
    def obter_estatisticas_videos(cls):
        """Obtém estatísticas de vídeos com cache"""
        cache_key = 'estatisticas_videos_historia'
        estatisticas = cache.get(cache_key)
        
        if estatisticas is None:
            total_videos = cls.objects.count()
            videos_ativos = cls.objects.filter(ativo=True).count()
            videos_inativos = cls.objects.filter(ativo=False).count()
            video_principal = cls.objects.filter(principal=True, ativo=True).exists()
            
            # Contagem por formato
            por_formato = {}
            for formato_val, formato_label in cls.FORMATO_VIDEO_CHOICES:
                count = cls.objects.filter(formato_video=formato_val).count()
                por_formato[formato_val] = {
                    'label': formato_label,
                    'count': count
                }
            
            estatisticas = {
                'total_videos': total_videos,
                'videos_ativos': videos_ativos,
                'videos_inativos': videos_inativos,
                'video_principal': video_principal,
                'por_formato': por_formato,
                'tem_youtube': cls.objects.filter(url_youtube__isnull=False).exclude(url_youtube='').exists(),
            }
            cache.set(cache_key, estatisticas, 3600)  # Cache por 1 hora
        
        return estatisticas
    
    @classmethod
    def obter_video_por_id(cls, video_id):
        """Obtém vídeo por ID com cache"""
        cache_key = f'video_historia_id_{video_id}'
        video = cache.get(cache_key)
        
        if video is None:
            try:
                video = cls.objects.get(id=video_id)
                cache.set(cache_key, video, 3600)  # Cache por 1 hora
            except cls.DoesNotExist:
                cache.set(cache_key, None, 300)  # Cache negativo por 5 minutos
                return None
        return video
    
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
        
        # Se este vídeo for marcado como principal, desmarca outros
        if self.principal and self.ativo:
            VideoHistoria.objects.filter(principal=True).exclude(pk=self.pk).update(principal=False)
        
        super().save(*args, **kwargs)
        self.limpar_cache_video()
    
    @property
    def is_youtube(self):
        """Cache para verificação se é YouTube"""
        cache_key = f'video_{self.id}_is_youtube'
        is_youtube = cache.get(cache_key)
        
        if is_youtube is None:
            is_youtube = bool(self.url_youtube)
            cache.set(cache_key, is_youtube, 3600)  # Cache por 1 hora
        
        return is_youtube
    
    def get_video_url(self):
        """Cache para URL do vídeo"""
        cache_key = f'video_{self.id}_url'
        video_url = cache.get(cache_key)
        
        if video_url is None:
            if self.url_youtube:
                video_url = self.url_youtube
            elif self.arquivo_video:
                video_url = self.arquivo_video.url
            else:
                video_url = None
            cache.set(cache_key, video_url, 3600)  # Cache por 1 hora
        
        return video_url
    
    def get_thumbnail_url(self):
        """Cache para URL da thumbnail"""
        cache_key = f'video_{self.id}_thumbnail_url'
        thumbnail_url = cache.get(cache_key)
        
        if thumbnail_url is None:
            if self.thumbnail and self.thumbnail.name:
                thumbnail_url = self.thumbnail.url
            else:
                # Thumbnail padrão ou gerada do YouTube
                if self.is_youtube:
                    # Extrair thumbnail do YouTube (implementação básica)
                    try:
                        video_id = self.url_youtube.split('v=')[-1].split('&')[0]
                        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                    except:
                        thumbnail_url = '/static/img/video_placeholder.jpg'
                else:
                    thumbnail_url = '/static/img/video_placeholder.jpg'
            cache.set(cache_key, thumbnail_url, 3600)  # Cache por 1 hora
        
        return thumbnail_url
    
    def get_mime_type(self):
        """Cache para MIME type"""
        cache_key = f'video_{self.id}_mime_type'
        mime_type = cache.get(cache_key)
        
        if mime_type is None:
            mime_types = {
                'mp4': 'video/mp4',
                'webm': 'video/webm',
                'ogg': 'video/ogg'
            }
            mime_type = mime_types.get(self.formato_video, 'video/mp4')
            cache.set(cache_key, mime_type, 3600)  # Cache por 1 hora
        
        return mime_type
    
    def get_info_completa(self):
        """Obtém informações completas do vídeo com cache"""
        cache_key = f'video_{self.id}_info_completa'
        info = cache.get(cache_key)
        
        if info is None:
            info = {
                'id': self.id,
                'titulo': self.titulo,
                'descricao': self.descricao,
                'formato_video': self.formato_video,
                'is_youtube': self.is_youtube,
                'video_url': self.get_video_url(),
                'thumbnail_url': self.get_thumbnail_url(),
                'mime_type': self.get_mime_type(),
                'principal': self.principal,
                'ativo': self.ativo,
                'ordem_exibicao': self.ordem_exibicao,
                'data_criacao': self.data_criacao,
                'data_atualizacao': self.data_atualizacao,
            }
            cache.set(cache_key, info, 1800)  # Cache por 30 minutos
        
        return info
    
    def limpar_cache_video(self):
        """Limpa todo o cache relacionado a este vídeo"""
        cache_keys = [
            f'video_historia_id_{self.id}',
            f'video_{self.id}_is_youtube',
            f'video_{self.id}_url',
            f'video_{self.id}_thumbnail_url',
            f'video_{self.id}_mime_type',
            f'video_{self.id}_info_completa',
            'videos_historia_ativos',
            'video_historia_principal',
            'estatisticas_videos_historia',
            f'videos_historia_formato_{self.formato_video}',
            'videos_historia_recentes_5',
            'videos_historia_recentes_10',
        ]
        cache.delete_many(cache_keys)
    
    def delete(self, *args, **kwargs):
        """Limpa cache antes de deletar"""
        self.limpar_cache_video()
        super().delete(*args, **kwargs)

# Signal handlers para limpeza automática de cache
@receiver([post_save, post_delete], sender=VideoHistoria)
def limpar_cache_video_signals(sender, instance, **kwargs):
    """Limpa caches globais quando vídeos são modificados"""
    instance.limpar_cache_video()

# Funções utilitárias com cache
def obter_galeria_videos(limite=None):
    """Obtém galeria completa de vídeos com cache"""
    cache_key = f'galeria_videos_{limite if limite else "all"}'
    galeria = cache.get(cache_key)
    
    if galeria is None:
        videos = VideoHistoria.obter_videos_ativos()
        if limite:
            videos = videos[:limite]
        
        galeria = []
        for video in videos:
            galeria.append(video.get_info_completa())
        
        cache.set(cache_key, galeria, 1800)  # Cache por 30 minutos
    
    return galeria

def obter_videos_para_carrossel(limite=3):
    """Obtém vídeos para carrossel com cache"""
    cache_key = f'videos_carrossel_{limite}'
    videos = cache.get(cache_key)
    
    if videos is None:
        # Prioriza vídeo principal e depois por ordem de exibição
        video_principal = VideoHistoria.obter_video_principal()
        outros_videos = VideoHistoria.obter_videos_ativos()
        
        if video_principal:
            outros_videos = [v for v in outros_videos if v.id != video_principal.id]
        
        videos = [video_principal] if video_principal else []
        videos.extend(outros_videos[:limite - (1 if video_principal else 0)])
        
        cache.set(cache_key, videos, 1800)  # Cache por 30 minutos
    
    return videos

def obter_proximo_video(video_atual):
    """Obtém próximo vídeo na sequência com cache"""
    cache_key = f'proximo_video_{video_atual.id}'
    proximo_video = cache.get(cache_key)
    
    if proximo_video is None:
        try:
            proximo_video = VideoHistoria.objects.filter(
                ativo=True,
                ordem_exibicao__gt=video_atual.ordem_exibicao
            ).order_by('ordem_exibicao').first()
            
            # Se não encontrou pelo ordem_exibicao, pega o próximo pela data
            if not proximo_video:
                proximo_video = VideoHistoria.objects.filter(
                    ativo=True,
                    data_criacao__gt=video_atual.data_criacao
                ).order_by('data_criacao').first()
            
            cache.set(cache_key, proximo_video, 3600)  # Cache por 1 hora
        except:
            proximo_video = None
            cache.set(cache_key, None, 300)  # Cache negativo por 5 minutos
    
    return proximo_video

def obter_video_anterior(video_atual):
    """Obtém vídeo anterior na sequência com cache"""
    cache_key = f'video_anterior_{video_atual.id}'
    video_anterior = cache.get(cache_key)
    
    if video_anterior is None:
        try:
            video_anterior = VideoHistoria.objects.filter(
                ativo=True,
                ordem_exibicao__lt=video_atual.ordem_exibicao
            ).order_by('-ordem_exibicao').first()
            
            # Se não encontrou pelo ordem_exibicao, pega o anterior pela data
            if not video_anterior:
                video_anterior = VideoHistoria.objects.filter(
                    ativo=True,
                    data_criacao__lt=video_atual.data_criacao
                ).order_by('-data_criacao').first()
            
            cache.set(cache_key, video_anterior, 3600)  # Cache por 1 hora
        except:
            video_anterior = None
            cache.set(cache_key, None, 300)  # Cache negativo por 5 minutos
    
    return video_anterior

# Função para limpar todo o cache de vídeos (útil para admin)
def limpar_cache_videos_global():
    """Limpa todo o cache relacionado a vídeos"""
    cache.delete_many([
        'videos_historia_ativos',
        'video_historia_principal',
        'estatisticas_videos_historia',
        'galeria_videos_all',
        'galeria_videos_10',
        'videos_carrossel_3',
        'videos_carrossel_5',
    ])