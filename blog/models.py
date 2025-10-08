from django.db import models
from django.conf import settings  # Importar settings
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator

# Remova esta linha:
# from django.contrib.auth.models import User

class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
    
    def __str__(self):
        return self.nome

class Publicacao(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    conteudo = models.TextField()
    resumo = models.TextField(max_length=300)
    # CORREÇÃO: Use settings.AUTH_USER_MODEL em vez de User
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    imagem_destaque = models.ImageField(upload_to='blog/', blank=True, null=True)
    data_publicacao = models.DateTimeField(default=timezone.now)
    data_atualizacao = models.DateTimeField(auto_now=True)
    publicado = models.BooleanField(default=False)
    visualizacoes = models.PositiveIntegerField(default=0)
    
    # Avaliações - CORREÇÃO: Use settings.AUTH_USER_MODEL
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
        from django.urls import reverse
        return reverse('detalhes_publicacao', kwargs={'pk': self.id})
    
    def total_comentarios(self):
        return self.comentarios.count()
    
    def total_likes(self):
        return self.likes.count()
    
    def total_adores(self):
        return self.adores.count()
    
    def incrementar_visualizacao(self):
        self.visualizacoes += 1
        self.save()
    
    def get_postagens_relacionadas(self):
        return Publicacao.objects.filter(
            categoria=self.categoria,
            publicado=True
        ).exclude(id=self.id).order_by('-data_publicacao')[:3]

class Comentario(models.Model):
    publicacao = models.ForeignKey(Publicacao, on_delete=models.CASCADE, related_name='comentarios')
    # CORREÇÃO: Use settings.AUTH_USER_MODEL em vez de User
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    texto = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    # Avaliação do comentário - CORREÇÃO: Use settings.AUTH_USER_MODEL
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
        return self.likes.count()
    def __str__(self):
        return f'Comentário de {self.autor} em {self.publicacao}'
    
    def total_likes(self):
        return self.likes.count()
    
    def usuario_curtiu(self, usuario):
        """Verifica se o usuário curtiu este comentário"""
        return self.likes.filter(id=usuario.id).exists()

class Avaliacao(models.Model):
    publicacao = models.ForeignKey(Publicacao, on_delete=models.CASCADE, related_name='avaliacoes')
    # CORREÇÃO: Use settings.AUTH_USER_MODEL em vez de User
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