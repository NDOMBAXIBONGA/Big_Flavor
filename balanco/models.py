# balanco/models.py
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

def data_hoje():
    """Função para retornar a data atual"""
    return timezone.now().date()

class RelatorioBalanco(models.Model):
    """Model para gerar relatórios de balanço personalizados por período"""
    
    nome_relatorio = models.CharField(
        max_length=100,
        verbose_name='Nome do Relatório',
        default='Relatório Personalizado'
    )
    
    data_inicio = models.DateField(
        verbose_name='Data de Início',
        default=data_hoje
    )
    
    data_fim = models.DateField(
        verbose_name='Data de Término',
        default=data_hoje
    )
    
    # Campos calculados
    total_pedidos_entregues = models.IntegerField(
        default=0,
        verbose_name='Pedidos Entregues'
    )
    
    total_pedidos_cancelados = models.IntegerField(
        default=0,
        verbose_name='Pedidos Cancelados'
    )
    
    # MODIFICADO: Subtotal (soma de TODOS os pedidos, incluindo cancelados)
    subtotal_pedidos = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name='Subtotal (Todos os Pedidos)'
    )
    
    # NOVO CAMPO: Valor total dos pedidos cancelados
    valor_total_cancelados = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name='Valor Total Cancelado'
    )
    
    # MODIFICADO: Total Geral (Subtotal - Cancelados)
    total_geral = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name='Total Geral (Subtotal - Cancelados)'
    )
    
    total_pedidos_periodo = models.IntegerField(
        default=0,
        verbose_name='Total de Pedidos no Período'
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Relatório de Balanço'
        verbose_name_plural = 'Relatórios de Balanço'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f"Relatório {self.nome_relatorio} - {self.data_inicio} a {self.data_fim}"
    
    def buscar_dados_carrinho(self):
        """Busca dados do carrinho no período especificado"""
        from carinho.models import PedidoEntrega
        
        inicio_periodo = timezone.make_aware(
            datetime.combine(self.data_inicio, datetime.min.time())
        )
        fim_periodo = timezone.make_aware(
            datetime.combine(self.data_fim, datetime.max.time())
        )
        
        print(f"🔍 Buscando pedidos de {inicio_periodo} até {fim_periodo}")
        
        pedidos_periodo = PedidoEntrega.objects.filter(
            data_solicitacao__range=(inicio_periodo, fim_periodo)
        )
        
        print(f"📦 Total de pedidos encontrados: {pedidos_periodo.count()}")
        
        self._calcular_estatisticas(pedidos_periodo)
        self.save()
        
        return self
    
    def _calcular_estatisticas(self, pedidos_queryset):
        """Calcula estatísticas a partir dos pedidos"""
        pedidos_entregues = pedidos_queryset.filter(estado='entregue')
        self.total_pedidos_entregues = pedidos_entregues.count()
        
        pedidos_cancelados = pedidos_queryset.filter(estado='cancelado')
        self.total_pedidos_cancelados = pedidos_cancelados.count()
        
        # NOVO CÁLCULO: Subtotal (soma de TODOS os pedidos, incluindo cancelados)
        self.subtotal_pedidos = Decimal('0.00')
        for pedido in pedidos_queryset:
            try:
                self.subtotal_pedidos += pedido.total_pedido
            except Exception as e:
                print(f"⚠️ Erro ao calcular subtotal do pedido {pedido.id}: {e}")
                continue
        
        # NOVO CÁLCULO: Valor total dos pedidos cancelados
        self.valor_total_cancelados = Decimal('0.00')
        for pedido in pedidos_cancelados:
            try:
                self.valor_total_cancelados += pedido.total_pedido
            except Exception as e:
                print(f"⚠️ Erro ao calcular valor cancelado do pedido {pedido.id}: {e}")
                continue
        
        # NOVO CÁLCULO: Total Geral (Subtotal - Valor Cancelado)
        self.total_geral = self.subtotal_pedidos - self.valor_total_cancelados
        
        self.total_pedidos_periodo = pedidos_queryset.count()
        
        print(f"✅ Estatísticas calculadas:")
        print(f"   - Pedidos entregues: {self.total_pedidos_entregues}")
        print(f"   - Pedidos cancelados: {self.total_pedidos_cancelados}")
        print(f"   - Subtotal (todos pedidos): R$ {self.subtotal_pedidos}")
        print(f"   - Valor total cancelado: R$ {self.valor_total_cancelados}")
        print(f"   - Total geral: R$ {self.total_geral}")
        print(f"   - Total pedidos no período: {self.total_pedidos_periodo}")
    
    # PROPRIEDADES PARA CÁLCULOS
    @property
    def taxa_sucesso(self):
        """Taxa de pedidos entregues com sucesso"""
        if self.total_pedidos_periodo == 0:
            return 0
        return (self.total_pedidos_entregues / self.total_pedidos_periodo) * 100
    
    @property
    def taxa_cancelamento(self):
        """Taxa de pedidos cancelados"""
        if self.total_pedidos_periodo == 0:
            return 0
        return (self.total_pedidos_cancelados / self.total_pedidos_periodo) * 100
    
    @property
    def taxa_cancelamento_valor(self):
        """NOVA PROPRIEDADE: Taxa de cancelamento em valor"""
        if self.subtotal_pedidos == 0:
            return 0
        return (self.valor_total_cancelados / self.subtotal_pedidos) * 100
    
    @property
    def valor_medio_entrega(self):
        """Valor médio por entrega"""
        if self.total_pedidos_entregues == 0:
            return Decimal('0.00')
        # Usa o valor dos pedidos entregues do subtotal
        valor_entregues = Decimal('0.00')
        from carinho.models import PedidoEntrega
        pedidos_entregues = PedidoEntrega.objects.filter(
            data_solicitacao__range=(
                timezone.make_aware(datetime.combine(self.data_inicio, datetime.min.time())),
                timezone.make_aware(datetime.combine(self.data_fim, datetime.max.time()))
            ),
            estado='entregue'
        )
        for pedido in pedidos_entregues:
            try:
                valor_entregues += pedido.total_pedido
            except:
                continue
        return valor_entregues / self.total_pedidos_entregues
    
    @property
    def valor_medio_pedido(self):
        """NOVA PROPRIEDADE: Valor médio por pedido (considerando subtotal)"""
        if self.total_pedidos_periodo == 0:
            return Decimal('0.00')
        return self.subtotal_pedidos / self.total_pedidos_periodo
    
    @property
    def eficiencia_operacional(self):
        """NOVA PROPRIEDADE: Eficiência operacional (Total Geral / Subtotal)"""
        if self.subtotal_pedidos == 0:
            return 0
        return (self.total_geral / self.subtotal_pedidos) * 100
    
    @property
    def dias_periodo(self):
        """Número de dias no período"""
        return (self.data_fim - self.data_inicio).days + 1
    
    @property
    def pedidos_por_dia(self):
        """Média de pedidos por dia"""
        if self.dias_periodo == 0:
            return 0
        return self.total_pedidos_periodo / self.dias_periodo
    
    @property
    def valor_geral_por_dia(self):
        """NOVA PROPRIEDADE: Total geral por dia"""
        if self.dias_periodo == 0:
            return Decimal('0.00')
        return self.total_geral / self.dias_periodo
    
    @property
    def subtotal_por_dia(self):
        """NOVA PROPRIEDADE: Subtotal por dia"""
        if self.dias_periodo == 0:
            return Decimal('0.00')
        return self.subtotal_pedidos / self.dias_periodo