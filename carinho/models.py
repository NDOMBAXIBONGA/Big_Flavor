from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db import IntegrityError, transaction

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
        Método simplificado e seguro para obter carrinho aberto
        """
        try:
            return cls.objects.get(usuario=usuario, estado='aberto')
        except cls.DoesNotExist:
            try:
                return cls.objects.create(usuario=usuario, estado='aberto')
            except IntegrityError:
                return cls.objects.get(usuario=usuario, estado='aberto')
        except cls.MultipleObjectsReturned:
            carrinhos = cls.objects.filter(
                usuario=usuario, 
                estado='aberto'
            ).order_by('-data_criacao')
            
            carrinho_principal = carrinhos.first()
            carrinhos.exclude(id=carrinho_principal.id).update(estado='fechado')
            
            return carrinho_principal
    
    def __str__(self):
        """CORRIGIDO: User padrão não tem campo 'nome'"""
        nome_usuario = (
            f"{self.usuario.first_name} {self.usuario.last_name}".strip()
            or self.usuario.username
        )
        return f"Carrinho #{self.id} - {nome_usuario}"
    
    @property
    def total_itens(self):
        return self.itens.aggregate(total=models.Sum('quantidade'))['total'] or 0
    
    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.itens.all())
    
    @property
    def taxa_entrega(self):
        if self.subtotal >= Decimal('5000.00'):
            return Decimal('0.00')
        return Decimal('1000.00')
    
    @property
    def total(self):
        return self.subtotal + self.taxa_entrega
    
    def fechar_carrinho(self):
        self.estado = 'fechado'
        self.save()

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
        return self.produto.preco * self.quantidade

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
    
    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            self.numero_pedido = f"P{self.carrinho.usuario.id:04d}-{self.carrinho.id:04d}"
        super().save(*args, **kwargs)