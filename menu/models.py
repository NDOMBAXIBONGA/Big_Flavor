from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from decimal import Decimal

class Produto(models.Model):
    CATEGORIA_CHOICES = [
        ('hamburguer', 'hamburguer'),
        ('Lanches', 'Lanches'),
        ('Bebidas', 'Bebidas'),
    ]
    
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
        ('esgotado', 'Esgotado'),
    ]
    
    nome = models.CharField(
        max_length=200,
        verbose_name='Nome do Produto'
    )
    
    descricao = models.TextField(
        verbose_name='Descrição',
        blank=True
    )
    
    descricao_curta = models.CharField(
        max_length=300,
        verbose_name='Descrição Curta',
        blank=True
    )
    
    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Preço',
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        verbose_name='Categoria'
    )
    
    imagem = models.ImageField(
        upload_to='produtos/',
        verbose_name='Imagem',
        blank=True,
        null=True,
        help_text='Formatos suportados: JPG, PNG, GIF'
    )
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem de Exibição',
        help_text='Define a ordem de exibição dos produtos (menor número aparece primeiro)'
    )

    def get_imagem_url(self):
        """Retorna a URL da imagem ou uma imagem padrão"""
        if self.imagem and hasattr(self.imagem, 'url'):
            return self.imagem.url
        return '/static/images/sem-imagem.jpg'  # Imagem padrão
    
    estoque = models.PositiveIntegerField(
        default=0,
        verbose_name='Quantidade em Estoque'
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ativo',
        verbose_name='Status'
    )
    
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Criação'
    )
    
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Atualização'
    )

    class Meta:
        ordering = ['ordem', 'nome']  # Ordena por ordem e depois por nome
    
    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return self.nome
    
    def get_absolute_url(self):
        return reverse('detalhes_produto', kwargs={'pk': self.pk})
    
    def get_preco_formatado(self):
        return f"KZ {self.preco:.2f}"
    
    def em_estoque(self):
        return self.estoque > 0 and self.status == 'ativo'
    
    def get_badge_status(self):
        status_classes = {
            'ativo': 'bg-success',
            'inativo': 'bg-secondary',
            'esgotado': 'bg-danger'
        }
        return status_classes.get(self.status, 'bg-secondary')