from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
    
    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        # Limpa cache relacionado quando uma categoria é salva
        cache.delete_many([
            'todas_categorias',
            f'categoria_{self.slug}',
            'publicacoes_recentes',
            'publicacoes_populares'
        ])
        super().save(*args, **kwargs)

class Publicacao(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    conteudo = models.TextField()
    resumo = models.TextField(max_length=300)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    imagem_destaque = models.ImageField(upload_to='blog/', blank=True, null=True)
    data_publicacao = models.DateTimeField(default=timezone.now)
    data_atualizacao = models.DateTimeField(auto_now=True)
    publicado = models.BooleanField(default=False)
    visualizacoes = models.PositiveIntegerField(default=0)
    
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='post_likes', 
        blank=True
    )
    adores = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='post_adores', 
        blank=True
    )
    
    class Meta:
        ordering = ['-data_publicacao']
        verbose_name = 'Publicação'
        verbose_name_plural = 'Publicações'
    
    def __str__(self):
        return self.titulo
    
    def get_absolute_url(self):
        return reverse('detalhes_publicacao', kwargs={'pk': self.id})
    
    def total_comentarios(self):
        # Cache para total de comentários
        cache_key = f'publicacao_{self.id}_total_comentarios'
        total = cache.get(cache_key)
        if total is None:
            total = self.comentarios.count()
            cache.set(cache_key, total, 300)  # Cache por 5 minutos
        return total
    
    def total_likes(self):
        cache_key = f'publicacao_{self.id}_total_likes'
        total = cache.get(cache_key)
        if total is None:
            total = self.likes.count()
            cache.set(cache_key, total, 300)
        return total
    
    def total_adores(self):
        cache_key = f'publicacao_{self.id}_total_adores'
        total = cache.get(cache_key)
        if total is None:
            total = self.adores.count()
            cache.set(cache_key, total, 300)
        return total
    
    def incrementar_visualizacao(self):
        self.visualizacoes += 1
        self.save()
        # Limpa cache de publicações populares
        cache.delete('publicacoes_populares')
    
    def get_postagens_relacionadas(self):
        if not self.categoria:
            return Publicacao.objects.none()
        
        cache_key = f'publicacao_{self.id}_relacionadas'
        relacionadas = cache.get(cache_key)
        
        if relacionadas is None:
            relacionadas = Publicacao.objects.filter(
                categoria=self.categoria,
                publicado=True
            ).exclude(id=self.id).order_by('-data_publicacao')[:3]
            cache.set(cache_key, relacionadas, 3600)  # Cache por 1 hora
        
        return relacionadas
    
    def save(self, *args, **kwargs):
        # Limpa cache relacionado quando uma publicação é salva
        cache_keys_to_delete = [
            'publicacoes_recentes',
            'publicacoes_populares',
            f'publicacao_{self.id}_relacionadas',
            f'categoria_{self.categoria.slug}_publicacoes' if self.categoria else None
        ]
        
        # Remove keys None
        cache_keys_to_delete = [key for key in cache_keys_to_delete if key is not None]
        cache.delete_many(cache_keys_to_delete)
        
        super().save(*args, **kwargs)

class Comentario(models.Model):
    publicacao = models.ForeignKey(Publicacao, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    texto = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='comentario_likes', 
        blank=True
    )
    
    class Meta:
        ordering = ['-data_criacao']
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'
    
    def __str__(self):
        return f'Comentário de {self.autor} em {self.publicacao}'
    
    def total_likes_comentario(self):
        cache_key = f'comentario_{self.id}_total_likes'
        total = cache.get(cache_key)
        if total is None:
            total = self.likes.count()
            cache.set(cache_key, total, 300)
        return total
    
    def total_likes(self):
        return self.total_likes_comentario()
    
    def usuario_curtiu(self, usuario):
        """Verifica se o usuário curtiu este comentário"""
        cache_key = f'comentario_{self.id}_usuario_{usuario.id}_curtiu'
        curtiu = cache.get(cache_key)
        if curtiu is None:
            curtiu = self.likes.filter(id=usuario.id).exists()
            cache.set(cache_key, curtiu, 300)
        return curtiu
    
    def save(self, *args, **kwargs):
        # Limpa cache relacionado quando um comentário é salvo
        cache.delete_many([
            f'publicacao_{self.publicacao.id}_total_comentarios',
            f'publicacao_{self.publicacao.id}_comentarios'
        ])
        super().save(*args, **kwargs)

class Avaliacao(models.Model):
    publicacao = models.ForeignKey(Publicacao, on_delete=models.CASCADE, related_name='avaliacoes')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nota = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['publicacao', 'usuario']
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
    
    def __str__(self):
        return f'{self.nota} estrelas por {self.usuario}'
    
    def save(self, *args, **kwargs):
        # Limpa cache de avaliações quando uma avaliação é salva
        cache.delete_many([
            f'publicacao_{self.publicacao.id}_media_avaliacoes',
            f'publicacao_{self.publicacao.id}_total_avaliacoes'
        ])
        super().save(*args, **kwargs)

# Funções utilitárias de cache
def get_publicacoes_recentes(limit=5):
    """Obtém publicações recentes com cache"""
    cache_key = f'publicacoes_recentes_{limit}'
    publicacoes = cache.get(cache_key)
    
    if publicacoes is None:
        publicacoes = Publicacao.objects.filter(
            publicado=True
        ).select_related('autor', 'categoria').order_by('-data_publicacao')[:limit]
        cache.set(cache_key, publicacoes, 3600)  # Cache por 1 hora
    
    return publicacoes

def get_publicacoes_populares(limit=5):
    """Obtém publicações populares com cache"""
    cache_key = f'publicacoes_populares_{limit}'
    publicacoes = cache.get(cache_key)
    
    if publicacoes is None:
        publicacoes = Publicacao.objects.filter(
            publicado=True
        ).select_related('autor', 'categoria').order_by('-visualizacoes', '-data_publicacao')[:limit]
        cache.set(cache_key, publicacoes, 1800)  # Cache por 30 minutos
    
    return publicacoes

def get_todas_categorias():
    """Obtém todas as categorias com cache"""
    cache_key = 'todas_categorias'
    categorias = cache.get(cache_key)
    
    if categorias is None:
        categorias = Categoria.objects.all()
        cache.set(cache_key, categorias, 3600)  # Cache por 1 hora
    
    return categorias

# Signal handlers para limpar cache automaticamente
@receiver(post_save, sender=Publicacao)
@receiver(post_delete, sender=Publicacao)
def limpar_cache_publicacao(sender, instance, **kwargs):
    """Limpa cache relacionado a publicações"""
    cache.delete_many([
        'publicacoes_recentes',
        'publicacoes_populares',
        f'publicacao_{instance.id}_relacionadas',
        f'categoria_{instance.categoria.slug}_publicacoes' if instance.categoria else None
    ])

@receiver(post_save, sender=Comentario)
@receiver(post_delete, sender=Comentario)
def limpar_cache_comentario(sender, instance, **kwargs):
    """Limpa cache relacionado a comentários"""
    cache.delete_many([
        f'publicacao_{instance.publicacao.id}_total_comentarios',
        f'publicacao_{instance.publicacao.id}_comentarios'
    ])

@receiver(post_save, sender=Categoria)
@receiver(post_delete, sender=Categoria)
def limpar_cache_categoria(sender, instance, **kwargs):
    """Limpa cache relacionado a categorias"""
    cache.delete_many([
        'todas_categorias',
        f'categoria_{instance.slug}',
        'publicacoes_recentes',
        'publicacoes_populares'
    ])