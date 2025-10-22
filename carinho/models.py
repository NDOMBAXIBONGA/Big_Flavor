from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db import IntegrityError


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
        Método para obter o carrinho aberto do usuário
        Sempre retorna um carrinho aberto, sem erros de duplicação
        """
        try:
            # Tenta encontrar um carrinho aberto existente
            return cls.objects.get(usuario=usuario, estado='aberto')
        except cls.DoesNotExist:
            # Se não existe, cria um novo
            try:
                return cls.objects.create(usuario=usuario, estado='aberto')
            except IntegrityError:
                # Em caso de race condition, busca novamente
                return cls.objects.get(usuario=usuario, estado='aberto')
        except cls.MultipleObjectsReturned:
            # Caso raro de múltiplos carrinhos, pega o mais recente
            return cls.objects.filter(usuario=usuario, estado='aberto').latest('data_criacao')
    
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
    
    def reabrir_carrinho(self):
        """Reabre um carrinho fechado, verificando constraints"""
        try:
            self.estado = 'aberto'
            self.save()
        except IntegrityError:
            # Se já existe um carrinho aberto, levanta erro
            raise ValueError("Já existe um carrinho aberto para este usuário")

    def __str__(self):
        return f"Carrinho #{self.id} - {self.usuario.nome}"

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
    
    def admin_display(self):
        return f"{self.quantidade}x {self.produto.nome} - KZ {self.subtotal:.2f}"
        
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
    
    # ADICIONAR: Campo para número do pedido
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
    
    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            # Contar quantos pedidos o cliente já tem e adicionar +1
            ultimo_numero = PedidoEntrega.objects.filter(
                carrinho__usuario=self.carrinho.usuario
            ).count()
            self.numero_pedido = f"P{self.carrinho.usuario.id:04d}-{(ultimo_numero + 1):04d}"
        super().save(*args, **kwargs)
    
    def itens_count(self):
        return self.carrinho.itens.count()
    itens_count.short_description = 'Nº de Itens'
    
    def listar_itens(self):
        return "\n".join([f"• {item.quantidade}x {item.produto.nome}" for item in self.carrinho.itens.all()])
    
    def __str__(self):
        # Usar o número do pedido se existir, caso contrário usar ID
        if self.numero_pedido:
            return f"Pedido {self.numero_pedido} - {self.carrinho.usuario.nome}"
        return f"Pedido #{self.id} - {self.carrinho.usuario.nome}"
    
    def get_badge_estado(self):
        estado_classes = {
            'pendente': 'bg-warning',
            'confirmado': 'bg-info',
            'preparacao': 'bg-primary',
            'despachado': 'bg-secondary',
            'entregue': 'bg-success',
            'cancelado': 'bg-danger',
        }
        return estado_classes.get(self.estado, 'bg-secondary')