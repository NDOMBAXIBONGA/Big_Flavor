from django.conf import settings
from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class Produto(models.Model):
    CATEGORIA_CHOICES = [
        ('hamburguer', 'Hambúrguer'),
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
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['ordem', 'nome']
    
    @classmethod
    def obter_produtos_ativos(cls):
        """Obtém produtos ativos com cache"""
        cache_key = 'produtos_ativos'
        produtos = cache.get(cache_key)
        
        if produtos is None:
            produtos = list(cls.objects.filter(status='ativo').order_by('ordem', 'nome'))
            cache.set(cache_key, produtos, 1800)  # Cache por 30 minutos
        
        return produtos
    
    @classmethod
    def obter_produtos_por_categoria(cls, categoria):
        """Obtém produtos por categoria com cache"""
        cache_key = f'produtos_categoria_{categoria}'
        produtos = cache.get(cache_key)
        
        if produtos is None:
            produtos = list(cls.objects.filter(
                categoria=categoria, 
                status='ativo'
            ).order_by('ordem', 'nome'))
            cache.set(cache_key, produtos, 1800)  # Cache por 30 minutos
        
        return produtos
    
    @classmethod
    def obter_produtos_em_estoque(cls):
        """Obtém produtos em estoque com cache"""
        cache_key = 'produtos_em_estoque'
        produtos = cache.get(cache_key)
        
        if produtos is None:
            produtos = list(cls.objects.filter(
                status='ativo',
                estoque__gt=0
            ).order_by('ordem', 'nome'))
            cache.set(cache_key, produtos, 900)  # Cache por 15 minutos
        
        return produtos
    
    @classmethod
    def obter_produtos_populares(cls, limite=8):
        """Obtém produtos populares com cache"""
        cache_key = f'produtos_populares_{limite}'
        produtos = cache.get(cache_key)
        
        if produtos is None:
            # Esta é uma implementação básica - você pode ajustar a lógica de popularidade
            produtos = list(cls.objects.filter(
                status='ativo',
                estoque__gt=0
            ).order_by('ordem', 'nome')[:limite])
            cache.set(cache_key, produtos, 3600)  # Cache por 1 hora
        
        return produtos
    
    @classmethod
    def obter_todas_categorias_com_produtos(cls):
        """Obtém todas as categorias com produtos ativos com cache"""
        cache_key = 'categorias_com_produtos'
        categorias = cache.get(cache_key)
        
        if categorias is None:
            from django.db.models import Count
            categorias = list(cls.objects.filter(
                status='ativo'
            ).values('categoria').annotate(
                total=Count('id')
            ).order_by('categoria'))
            cache.set(cache_key, categorias, 3600)  # Cache por 1 hora
        
        return categorias
    
    @classmethod
    def obter_estatisticas_produtos(cls):
        """Obtém estatísticas de produtos com cache"""
        cache_key = 'estatisticas_produtos'
        estatisticas = cache.get(cache_key)
        
        if estatisticas is None:
            total_produtos = cls.objects.count()
            produtos_ativos = cls.objects.filter(status='ativo').count()
            produtos_estoque = cls.objects.filter(estoque__gt=0).count()
            produtos_sem_estoque = cls.objects.filter(estoque=0).count()
            
            # Contagem por categoria
            por_categoria = {}
            for categoria_val, categoria_label in cls.CATEGORIA_CHOICES:
                count = cls.objects.filter(categoria=categoria_val).count()
                por_categoria[categoria_val] = {
                    'label': categoria_label,
                    'count': count
                }
            
            estatisticas = {
                'total_produtos': total_produtos,
                'produtos_ativos': produtos_ativos,
                'produtos_estoque': produtos_estoque,
                'produtos_sem_estoque': produtos_sem_estoque,
                'por_categoria': por_categoria,
            }
            cache.set(cache_key, estatisticas, 1800)  # Cache por 30 minutos
        
        return estatisticas
    
    @classmethod
    def obter_produto_por_id(cls, produto_id):
        """Obtém produto por ID com cache"""
        cache_key = f'produto_id_{produto_id}'
        produto = cache.get(cache_key)
        
        if produto is None:
            try:
                produto = cls.objects.get(id=produto_id)
                cache.set(cache_key, produto, 3600)  # Cache por 1 hora
            except cls.DoesNotExist:
                cache.set(cache_key, None, 300)  # Cache negativo por 5 minutos
                return None
        return produto
    
    @classmethod
    def buscar_produtos(cls, termo):
        """Busca produtos por termo com cache"""
        cache_key = f'busca_produtos_{termo.lower()}'
        produtos = cache.get(cache_key)
        
        if produtos is None:
            produtos = list(cls.objects.filter(
                models.Q(nome__icontains=termo) |
                models.Q(descricao__icontains=termo) |
                models.Q(descricao_curta__icontains=termo)
            ).filter(status='ativo').order_by('ordem', 'nome')[:50])
            cache.set(cache_key, produtos, 1800)  # Cache por 30 minutos
        
        return produtos

    def get_imagem_url(self):
        """Retorna a URL da imagem ou uma imagem padrão com cache"""
        cache_key = f'produto_{self.id}_imagem_url'
        imagem_url = cache.get(cache_key)
        
        if imagem_url is None:
            try:
                if self.imagem and self.imagem.name:
                    imagem_url = self.imagem.url
                else:
                    imagem_url = '/static/img/big.jpg'
                cache.set(cache_key, imagem_url, 3600)  # Cache por 1 hora
            except Exception as e:
                imagem_url = '/static/img/big.jpg'
                cache.set(cache_key, imagem_url, 3600)
        
        return imagem_url
    
    def __str__(self):
        return self.nome
    
    def get_absolute_url(self):
        return reverse('detalhes_produto', kwargs={'pk': self.pk})
    
    def get_preco_formatado(self):
        """Cache para preço formatado"""
        cache_key = f'produto_{self.id}_preco_formatado'
        preco_formatado = cache.get(cache_key)
        
        if preco_formatado is None:
            preco_formatado = f"KZ {self.preco:.2f}"
            cache.set(cache_key, preco_formatado, 3600)  # Cache por 1 hora
        
        return preco_formatado
    
    def em_estoque(self):
        """Cache para verificação de estoque"""
        cache_key = f'produto_{self.id}_em_estoque'
        em_estoque = cache.get(cache_key)
        
        if em_estoque is None:
            em_estoque = self.estoque > 0 and self.status == 'ativo'
            cache.set(cache_key, em_estoque, 300)  # Cache por 5 minutos (estoque muda rápido)
        
        return em_estoque
    
    def get_badge_status(self):
        """Cache para classe do badge de status"""
        cache_key = f'produto_{self.id}_badge_status'
        badge_class = cache.get(cache_key)
        
        if badge_class is None:
            status_classes = {
                'ativo': 'bg-success',
                'inativo': 'bg-secondary',
                'esgotado': 'bg-danger'
            }
            badge_class = status_classes.get(self.status, 'bg-secondary')
            cache.set(cache_key, badge_class, 3600)  # Cache por 1 hora
        
        return badge_class
    
    def get_info_completa(self):
        """Obtém informações completas do produto com cache"""
        cache_key = f'produto_{self.id}_info_completa'
        info = cache.get(cache_key)
        
        if info is None:
            info = {
                'id': self.id,
                'nome': self.nome,
                'descricao': self.descricao,
                'descricao_curta': self.descricao_curta,
                'preco': float(self.preco),
                'preco_formatado': self.get_preco_formatado(),
                'categoria': self.categoria,
                'imagem_url': self.get_imagem_url(),
                'estoque': self.estoque,
                'em_estoque': self.em_estoque(),
                'status': self.status,
                'badge_status': self.get_badge_status(),
                'data_criacao': self.data_criacao,
                'data_atualizacao': self.data_atualizacao,
            }
            cache.set(cache_key, info, 1800)  # Cache por 30 minutos
        
        return info
    
    def limpar_cache_produto(self):
        """Limpa todo o cache relacionado a este produto"""
        cache_keys = [
            f'produto_id_{self.id}',
            f'produto_{self.id}_imagem_url',
            f'produto_{self.id}_preco_formatado',
            f'produto_{self.id}_em_estoque',
            f'produto_{self.id}_badge_status',
            f'produto_{self.id}_info_completa',
            'produtos_ativos',
            'produtos_em_estoque',
            'estatisticas_produtos',
            'categorias_com_produtos',
            f'produtos_categoria_{self.categoria}',
            'produtos_populares_8',
            'produtos_populares_12',
        ]
        cache.delete_many(cache_keys)
        
        # Limpa caches de busca que podem conter este produto
        # Em produção, você pode querer ser mais específico aqui
    
    def save(self, *args, **kwargs):
        """Sobrescreve save para limpar cache"""
        # Limpa cache antes de salvar se for uma atualização
        if self.pk:
            try:
                produto_antigo = Produto.objects.get(pk=self.pk)
                # Se categoria mudou, limpa caches específicos
                if produto_antigo.categoria != self.categoria:
                    cache.delete(f'produtos_categoria_{produto_antigo.categoria}')
            except Produto.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        self.limpar_cache_produto()
    
    def delete(self, *args, **kwargs):
        """Limpa cache antes de deletar"""
        self.limpar_cache_produto()
        super().delete(*args, **kwargs)

class Favorito(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    produto = models.ForeignKey('menu.Produto', on_delete=models.CASCADE)
    data_adicao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['usuario', 'produto']
    
    @classmethod
    def obter_favoritos_usuario(cls, usuario):
        """Obtém favoritos do usuário com cache"""
        cache_key = f'favoritos_usuario_{usuario.id}'
        favoritos = cache.get(cache_key)
        
        if favoritos is None:
            favoritos = list(cls.objects.filter(usuario=usuario).select_related('produto'))
            cache.set(cache_key, favoritos, 1800)  # Cache por 30 minutos
        
        return favoritos
    
    @classmethod
    def obter_total_favoritos_usuario(cls, usuario):
        """Obtém total de favoritos do usuário com cache"""
        cache_key = f'total_favoritos_usuario_{usuario.id}'
        total = cache.get(cache_key)
        
        if total is None:
            total = cls.objects.filter(usuario=usuario).count()
            cache.set(cache_key, total, 900)  # Cache por 15 minutos
        
        return total
    
    @classmethod
    def usuario_tem_favorito(cls, usuario, produto):
        """Verifica se usuário tem produto como favorito com cache"""
        cache_key = f'usuario_{usuario.id}_favorito_produto_{produto.id}'
        tem_favorito = cache.get(cache_key)
        
        if tem_favorito is None:
            tem_favorito = cls.objects.filter(usuario=usuario, produto=produto).exists()
            cache.set(cache_key, tem_favorito, 1800)  # Cache por 30 minutos
        
        return tem_favorito
    
    @property
    def produto_em_estoque(self):
        """Cache para verificação se produto favorito está em estoque"""
        cache_key = f'favorito_{self.id}_produto_em_estoque'
        em_estoque = cache.get(cache_key)
        
        if em_estoque is None:
            em_estoque = self.produto.em_estoque()
            cache.set(cache_key, em_estoque, 300)  # Cache por 5 minutos
        
        return em_estoque
    
    def limpar_cache_favorito(self):
        """Limpa cache relacionado a este favorito"""
        cache_keys = [
            f'favoritos_usuario_{self.usuario.id}',
            f'total_favoritos_usuario_{self.usuario.id}',
            f'usuario_{self.usuario.id}_favorito_produto_{self.produto.id}',
            f'favorito_{self.id}_produto_em_estoque',
        ]
        cache.delete_many(cache_keys)
    
    def save(self, *args, **kwargs):
        """Sobrescreve save para limpar cache"""
        super().save(*args, **kwargs)
        self.limpar_cache_favorito()
        # Também limpa cache do produto relacionado
        self.produto.limpar_cache_produto()
    
    def delete(self, *args, **kwargs):
        """Limpa cache antes de deletar"""
        usuario_id = self.usuario.id
        produto_id = self.produto.id
        
        super().delete(*args, **kwargs)
        
        # Limpa cache após deletar
        cache_keys = [
            f'favoritos_usuario_{usuario_id}',
            f'total_favoritos_usuario_{usuario_id}',
            f'usuario_{usuario_id}_favorito_produto_{produto_id}',
        ]
        cache.delete_many(cache_keys)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.produto.nome}"

# Signal handlers para limpeza automática de cache
@receiver([post_save, post_delete], sender=Produto)
def limpar_cache_produto_signals(sender, instance, **kwargs):
    """Limpa caches globais quando produtos são modificados"""
    instance.limpar_cache_produto()

@receiver([post_save, post_delete], sender=Favorito)
def limpar_cache_favorito_signals(sender, instance, **kwargs):
    """Limpa caches globais quando favoritos são modificados"""
    instance.limpar_cache_favorito()

# Funções utilitárias com cache
def obter_produtos_recomendados(usuario, limite=6):
    """Obtém produtos recomendados com cache"""
    cache_key = f'produtos_recomendados_usuario_{usuario.id}_{limite}'
    produtos = cache.get(cache_key)
    
    if produtos is None:
        # Lógica básica de recomendação - pode ser melhorada
        # Por enquanto, retorna produtos da mesma categoria dos favoritos
        categorias_favoritas = Favorito.objects.filter(
            usuario=usuario
        ).values_list('produto__categoria', flat=True).distinct()
        
        if categorias_favoritas:
            produtos = list(Produto.objects.filter(
                categoria__in=categorias_favoritas,
                status='ativo',
                estoque__gt=0
            ).exclude(
                favorito__usuario=usuario  # Exclui já favoritados
            ).order_by('?')[:limite])  # Ordem aleatória
        else:
            # Se não tem favoritos, retorna produtos populares
            produtos = Produto.obter_produtos_populares(limite)
        
        cache.set(cache_key, produtos, 3600)  # Cache por 1 hora
    
    return produtos

def obter_produtos_mais_favoritados(limite=10):
    """Obtém produtos mais favoritados com cache"""
    cache_key = f'produtos_mais_favoritados_{limite}'
    produtos = cache.get(cache_key)
    
    if produtos is None:
        from django.db.models import Count
        produtos = list(Produto.objects.filter(
            favorito__isnull=False
        ).annotate(
            total_favoritos=Count('favorito')
        ).order_by('-total_favoritos')[:limite])
        cache.set(cache_key, produtos, 7200)  # Cache por 2 horas
    
    return produtos