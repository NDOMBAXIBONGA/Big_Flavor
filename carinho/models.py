from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db import IntegrityError, transaction
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class Carrinho(models.Model):
    ESTADO_CHOICES = [
        ('aberto', 'Aberto'),
        ('fechado', 'Fechado'),
        ('cancelado', 'Cancelado'),
    ]
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Cliente'
    )
    
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Criação'
    )
    
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Atualização'
    )
    
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='aberto',
        verbose_name='Estado do Carrinho'
    )
    
    class Meta:
        verbose_name = 'Carrinho'
        verbose_name_plural = 'Carrinhos'
        ordering = ['-data_criacao']
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'estado'],
                condition=models.Q(estado='aberto'),
                name='carrinho_aberto_unico_por_usuario'
            )
        ]
    
    @classmethod
    def obter_carrinho_aberto(cls, usuario):
        """
        Método simplificado e seguro para obter carrinho aberto com cache
        """
        cache_key = f'carrinho_aberto_usuario_{usuario.id}'
        carrinho = cache.get(cache_key)
        
        if carrinho is None:
            try:
                carrinho = cls.objects.get(usuario=usuario, estado='aberto')
                # Cache por 30 minutos
                cache.set(cache_key, carrinho, 1800)
            except cls.DoesNotExist:
                try:
                    carrinho = cls.objects.create(usuario=usuario, estado='aberto')
                    cache.set(cache_key, carrinho, 1800)
                except IntegrityError:
                    carrinho = cls.objects.get(usuario=usuario, estado='aberto')
                    cache.set(cache_key, carrinho, 1800)
            except cls.MultipleObjectsReturned:
                carrinhos = cls.objects.filter(
                    usuario=usuario, 
                    estado='aberto'
                ).order_by('-data_criacao')
                
                carrinho_principal = carrinhos.first()
                carrinhos.exclude(id=carrinho_principal.id).update(estado='fechado')
                
                carrinho = carrinho_principal
                cache.set(cache_key, carrinho, 1800)
        
        return carrinho
    
    def __str__(self):
        """CORRIGIDO: User padrão não tem campo 'nome'"""
        nome_usuario = (
            f"{self.usuario.first_name} {self.usuario.last_name}".strip()
            or self.usuario.username
        )
        return f"Carrinho #{self.id} - {nome_usuario}"
    
    @property
    def total_itens(self):
        """Cache para total de itens no carrinho"""
        cache_key = f'carrinho_{self.id}_total_itens'
        total = cache.get(cache_key)
        
        if total is None:
            total = self.itens.aggregate(total=models.Sum('quantidade'))['total'] or 0
            cache.set(cache_key, total, 300)  # 5 minutos
        
        return total
    
    @property
    def subtotal(self):
        """Cache para subtotal do carrinho"""
        cache_key = f'carrinho_{self.id}_subtotal'
        subtotal_cache = cache.get(cache_key)
        
        if subtotal_cache is None:
            subtotal_cache = sum(item.subtotal for item in self.itens.all())
            cache.set(cache_key, subtotal_cache, 300)  # 5 minutos
        
        return subtotal_cache
    
    @property
    def taxa_entrega(self):
        """Cache para taxa de entrega"""
        cache_key = f'carrinho_{self.id}_taxa_entrega'
        taxa = cache.get(cache_key)
        
        if taxa is None:
            if self.subtotal >= Decimal('5000.00'):
                taxa = Decimal('0.00')
            else:
                taxa = Decimal('1000.00')
            cache.set(cache_key, taxa, 300)  # 5 minutos
        
        return taxa
    
    @property
    def total(self):
        """Cache para total geral"""
        cache_key = f'carrinho_{self.id}_total'
        total_cache = cache.get(cache_key)
        
        if total_cache is None:
            total_cache = self.subtotal + self.taxa_entrega
            cache.set(cache_key, total_cache, 300)  # 5 minutos
        
        return total_cache
    
    def fechar_carrinho(self):
        """Fecha o carrinho e limpa cache relacionado"""
        self.estado = 'fechado'
        self.save()
        
        # Limpa todo o cache relacionado a este carrinho
        self.limpar_cache()
    
    def limpar_cache(self):
        """Limpa todo o cache relacionado a este carrinho"""
        cache_keys = [
            f'carrinho_aberto_usuario_{self.usuario.id}',
            f'carrinho_{self.id}_total_itens',
            f'carrinho_{self.id}_subtotal',
            f'carrinho_{self.id}_taxa_entrega',
            f'carrinho_{self.id}_total',
            f'carrinho_{self.id}_itens',
            f'usuario_{self.usuario.id}_carrinho_ativo'
        ]
        cache.delete_many(cache_keys)
    
    def save(self, *args, **kwargs):
        """Sobrescreve save para limpar cache quando necessário"""
        if self.pk:  # Se é uma atualização
            self.limpar_cache()
        super().save(*args, **kwargs)

class ItemCarrinho(models.Model):
    carrinho = models.ForeignKey(
        Carrinho,
        on_delete=models.CASCADE,
        related_name='itens'
    )
    
    produto = models.ForeignKey(
        'menu.Produto',
        on_delete=models.CASCADE
    )
    
    quantidade = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    
    data_adicao = models.DateTimeField(
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'Item do Carrinho'
        verbose_name_plural = 'Itens do Carrinho'
        ordering = ['-data_adicao']
        unique_together = ['carrinho', 'produto']
    
    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"
    
    @property
    def subtotal(self):
        """Cache para subtotal do item"""
        cache_key = f'item_carrinho_{self.id}_subtotal'
        subtotal = cache.get(cache_key)
        
        if subtotal is None:
            subtotal = self.produto.preco * self.quantidade
            cache.set(cache_key, subtotal, 300)  # 5 minutos
        
        return subtotal
    
    def limpar_cache(self):
        """Limpa cache relacionado a este item"""
        cache_keys = [
            f'item_carrinho_{self.id}_subtotal',
            f'carrinho_{self.carrinho.id}_total_itens',
            f'carrinho_{self.carrinho.id}_subtotal',
            f'carrinho_{self.carrinho.id}_taxa_entrega',
            f'carrinho_{self.carrinho.id}_total',
            f'carrinho_{self.carrinho.id}_itens'
        ]
        cache.delete_many(cache_keys)
    
    def save(self, *args, **kwargs):
        """Sobrescreve save para limpar cache"""
        super().save(*args, **kwargs)
        self.limpar_cache()
    
    def delete(self, *args, **kwargs):
        """Sobrescreve delete para limpar cache"""
        carrinho_id = self.carrinho.id
        super().delete(*args, **kwargs)
        
        # Limpa cache do carrinho após deletar item
        cache_keys = [
            f'carrinho_{carrinho_id}_total_itens',
            f'carrinho_{carrinho_id}_subtotal',
            f'carrinho_{carrinho_id}_taxa_entrega',
            f'carrinho_{carrinho_id}_total',
            f'carrinho_{carrinho_id}_itens'
        ]
        cache.delete_many(cache_keys)

class PedidoEntrega(models.Model):
    ESTADO_PEDIDO_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('preparacao', 'Em Preparação'),
        ('despachado', 'Despachado'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ]
    
    carrinho = models.OneToOneField(
        Carrinho,
        on_delete=models.CASCADE,
        related_name='pedido_entrega'
    )
    
    numero_pedido = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Número do Pedido'
    )
    
    endereco_entrega = models.TextField(
        verbose_name='Endereço de Entrega'
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações'
    )
    
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_PEDIDO_CHOICES,
        default='pendente',
        verbose_name='Estado do Pedido'
    )
    
    data_solicitacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Solicitação'
    )
    
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Atualização'
    )
    
    notificado_admin = models.BooleanField(
        default=False,
        verbose_name='Admin Notificado'
    )
    
    class Meta:
        verbose_name = 'Pedido de Entrega'
        verbose_name_plural = 'Pedidos de Entrega'
        ordering = ['-data_solicitacao']
    
    def __str__(self):
        """CORRIGIDO: User padrão não tem campo 'nome'"""
        nome_usuario = (
            f"{self.carrinho.usuario.first_name} {self.carrinho.usuario.last_name}".strip()
            or self.carrinho.usuario.username
        )
        if self.numero_pedido:
            return f"Pedido {self.numero_pedido} - {nome_usuario}"
        return f"Pedido #{self.id} - {nome_usuario}"
    
    @property
    def total_pedido(self):
        """Cache para total do pedido"""
        cache_key = f'pedido_{self.id}_total'
        total = cache.get(cache_key)
        
        if total is None:
            total = self.carrinho.total
            cache.set(cache_key, total, 600)  # 10 minutos
        
        return total
    
    @classmethod
    def obter_pedidos_ativos(cls):
        """Obtém pedidos ativos com cache"""
        cache_key = 'pedidos_ativos'
        pedidos = cache.get(cache_key)
        
        if pedidos is None:
            pedidos = cls.objects.filter(
                estado__in=['pendente', 'confirmado', 'preparacao', 'despachado']
            ).select_related(
                'carrinho__usuario'
            ).order_by('-data_solicitacao')
            cache.set(cache_key, pedidos, 300)  # 5 minutos
        
        return pedidos
    
    @classmethod
    def obter_pedidos_por_usuario(cls, usuario):
        """Obtém pedidos de um usuário com cache"""
        cache_key = f'pedidos_usuario_{usuario.id}'
        pedidos = cache.get(cache_key)
        
        if pedidos is None:
            pedidos = cls.objects.filter(
                carrinho__usuario=usuario
            ).select_related(
                'carrinho'
            ).order_by('-data_solicitacao')
            cache.set(cache_key, pedidos, 600)  # 10 minutos
        
        return pedidos
    
    def limpar_cache(self):
        """Limpa cache relacionado a este pedido"""
        cache_keys = [
            f'pedido_{self.id}_total',
            'pedidos_ativos',
            f'pedidos_usuario_{self.carrinho.usuario.id}',
            'estatisticas_pedidos',
            'total_pedidos_hoje'
        ]
        cache.delete_many(cache_keys)
    
    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            self.numero_pedido = f"P{self.carrinho.usuario.id:04d}-{self.carrinho.id:04d}"
        
        # Limpa cache antes de salvar se for atualização de estado
        if self.pk:
            pedido_antigo = PedidoEntrega.objects.get(pk=self.pk)
            if pedido_antigo.estado != self.estado:
                self.limpar_cache()
        
        super().save(*args, **kwargs)
        self.limpar_cache()

# Signal handlers para limpeza automática de cache
@receiver([post_save, post_delete], sender=ItemCarrinho)
def limpar_cache_item_carrinho(sender, instance, **kwargs):
    """Limpa cache quando itens do carrinho são modificados"""
    instance.limpar_cache()

@receiver([post_save, post_delete], sender=PedidoEntrega)
def limpar_cache_pedido(sender, instance, **kwargs):
    """Limpa cache quando pedidos são modificados"""
    instance.limpar_cache()

@receiver(post_save, sender=Carrinho)
def limpar_cache_carrinho(sender, instance, **kwargs):
    """Limpa cache quando carrinho é modificado"""
    instance.limpar_cache()

# Funções utilitárias com cache
def obter_estatisticas_pedidos():
    """Obtém estatísticas de pedidos com cache"""
    cache_key = 'estatisticas_pedidos'
    estatisticas = cache.get(cache_key)
    
    if estatisticas is None:
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        hoje = timezone.now().date()
        
        estatisticas = {
            'total_pedidos_hoje': PedidoEntrega.objects.filter(
                data_solicitacao__date=hoje
            ).count(),
            'pedidos_pendentes': PedidoEntrega.objects.filter(
                estado='pendente'
            ).count(),
            'pedidos_preparacao': PedidoEntrega.objects.filter(
                estado='preparacao'
            ).count(),
            'pedidos_despachados': PedidoEntrega.objects.filter(
                estado='despachado'
            ).count(),
        }
        cache.set(cache_key, estatisticas, 300)  # 5 minutos
    
    return estatisticas

def obter_carrinho_com_itens(usuario):
    """Obtém carrinho com itens relacionados usando cache"""
    cache_key = f'carrinho_com_itens_usuario_{usuario.id}'
    carrinho_data = cache.get(cache_key)
    
    if carrinho_data is None:
        carrinho = Carrinho.obter_carrinho_aberto(usuario)
        itens = carrinho.itens.select_related('produto').all()
        carrinho_data = {
            'carrinho': carrinho,
            'itens': itens,
            'total_itens': carrinho.total_itens,
            'subtotal': carrinho.subtotal,
            'total': carrinho.total
        }
        cache.set(cache_key, carrinho_data, 300)  # 5 minutos
    
    return carrinho_data