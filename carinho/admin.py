from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Carrinho, ItemCarrinho, PedidoEntrega

class EstadoCarrinhoFilter(admin.SimpleListFilter):
    title = 'Estado do Carrinho'
    parameter_name = 'estado'
    
    def lookups(self, request, model_admin):
        return [
            ('aberto', 'Carrinhos Abertos'),
            ('fechado', 'Carrinhos Fechados'),
            ('com_itens', 'Com Itens'),
            ('vazios', 'Vazios'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'aberto':
            return queryset.filter(estado='aberto')
        if self.value() == 'fechado':
            return queryset.filter(estado='fechado')
        if self.value() == 'com_itens':
            return queryset.filter(itens__isnull=False).distinct()
        if self.value() == 'vazios':
            return queryset.filter(itens__isnull=True)

class ItemCarrinhoInline(admin.TabularInline):
    """Inline para mostrar itens do carrinho"""
    model = ItemCarrinho
    extra = 0
    readonly_fields = ('produto', 'quantidade', 'subtotal', 'data_adicao')
    fields = ('produto', 'quantidade', 'subtotal', 'data_adicao')
    
    def subtotal(self, obj):
        return f"€{obj.subtotal:.2f}"
    subtotal.short_description = 'Subtotal'

@admin.register(ItemCarrinho)
class ItemCarrinhoAdmin(admin.ModelAdmin):
    list_display = ('id', 'carrinho', 'produto', 'quantidade', 'subtotal_display', 'data_adicao')
    list_filter = ('carrinho__estado', 'data_adicao', 'produto__categoria')
    search_fields = ('produto__nome', 'carrinho__usuario__email', 'carrinho__usuario__nome')
    readonly_fields = ('data_adicao', 'subtotal_display')
    list_per_page = 20
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('carrinho', 'produto', 'quantidade')
        }),
        ('Valores e Datas', {
            'fields': ('subtotal_display', 'data_adicao'),
            'classes': ('collapse',)
        }),
    )
    
    def subtotal_display(self, obj):
        return f"€{obj.subtotal:.2f}"
    subtotal_display.short_description = 'Subtotal'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('carrinho', 'produto')

class ItemCarrinhoPedidoInline(admin.TabularInline):
    """Inline para mostrar itens do carrinho através do PedidoEntrega"""
    model = ItemCarrinho
    extra = 0
    max_num = 0
    can_delete = False
    readonly_fields = ('produto', 'quantidade', 'preco_unitario', 'subtotal_display')
    fields = ('produto', 'quantidade', 'preco_unitario', 'subtotal_display')
    
    # Filtra apenas os itens do carrinho relacionado ao pedido
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Esta inline será usada através do PedidoEntrega, então filtra pelo carrinho do pedido
        return qs
    
    def preco_unitario(self, obj):
        return f"€{obj.produto.preco:.2f}"
    preco_unitario.short_description = 'Preço Unitário'
    
    def subtotal_display(self, obj):
        return f"€{obj.subtotal:.2f}"
    subtotal_display.short_description = 'Subtotal'
    
    def has_add_permission(self, request, obj):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Carrinho)
class CarrinhoAdmin(admin.ModelAdmin):
    list_filter = (EstadoCarrinhoFilter, 'data_criacao')
    list_display = ('id', 'usuario', 'estado', 'total_itens', 'subtotal_display', 'taxa_entrega_display', 'total_display', 'data_criacao')
    list_filter = ('estado', 'data_criacao')
    search_fields = ('usuario__email', 'usuario__nome')
    readonly_fields = ('data_criacao', 'data_atualizacao', 'subtotal_display', 'taxa_entrega_display', 'total_display', 'total_itens')
    inlines = [ItemCarrinhoInline]  # Aqui funciona porque Carrinho tem relação direta com ItemCarrinho
    list_per_page = 20
    
    fieldsets = (
        ('Informações do Cliente', {
            'fields': ('usuario', 'estado')
        }),
        ('Resumo Financeiro', {
            'fields': ('total_itens', 'subtotal_display', 'taxa_entrega_display', 'total_display')
        }),
        ('Datas', {
            'fields': ('data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )
    
    def subtotal_display(self, obj):
        return f"€{obj.subtotal:.2f}"
    subtotal_display.short_description = 'Subtotal'
    
    def taxa_entrega_display(self, obj):
        return f"€{obj.taxa_entrega:.2f}"
    taxa_entrega_display.short_description = 'Taxa de Entrega'
    
    def total_display(self, obj):
        return f"€{obj.total:.2f}"
    total_display.short_description = 'Total'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario').prefetch_related('itens__produto')

@admin.register(PedidoEntrega)
class PedidoEntregaAdmin(admin.ModelAdmin):
    list_display = ('id', 'carrinho_usuario', 'estado', 'total_pedido', 'data_solicitacao', 'notificado_admin')
    list_filter = ('estado', 'data_solicitacao', 'notificado_admin')
    search_fields = ('carrinho__usuario__email', 'carrinho__usuario__nome', 'endereco_entrega')
    readonly_fields = ('data_solicitacao', 'data_atualizacao', 'total_pedido_display', 'resumo_itens', 'lista_itens_detalhada')
    list_editable = ('estado', 'notificado_admin')
    # REMOVA o inline problemático e use métodos personalizados
    list_per_page = 20
    
    fieldsets = (
        ('Informações do Pedido', {
            'fields': ('carrinho', 'estado', 'notificado_admin')
        }),
        ('Informações de Entrega', {
            'fields': ('endereco_entrega', 'observacoes')
        }),
        ('Resumo Financeiro', {
            'fields': ('total_pedido_display', 'resumo_itens', 'lista_itens_detalhada')
        }),
        ('Datas', {
            'fields': ('data_solicitacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )
    
    def carrinho_usuario(self, obj):
        return f"{obj.carrinho.usuario.nome} ({obj.carrinho.usuario.email})"
    carrinho_usuario.short_description = 'Cliente'
    carrinho_usuario.admin_order_field = 'carrinho__usuario__email'
    
    def total_pedido(self, obj):
        return f"€{obj.carrinho.total:.2f}"
    total_pedido.short_description = 'Total'
    
    def total_pedido_display(self, obj):
        carrinho = obj.carrinho
        html = f"""
        <div style="background: #f8f9fa;color:black; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div style="font-size: 18px;">
                    <strong>Subtotal:</strong><br>
                    <strong>Taxa de Entrega:</strong><br>
                    <strong style="font-size: 20px;">Total Final:</strong>
                </div>
                <div style="font-size: 18px; text-align: right;">
                    KZ{carrinho.subtotal:.2f}<br>
                    KZ{carrinho.taxa_entrega:.2f}<br>
                    <strong style="font-size: 20px; color: #28a745;">KZ{carrinho.total:.2f}</strong>
                </div>
            </div>
        </div>
        """
        return mark_safe(html)
    total_pedido_display.short_description = 'Resumo Financeiro'

    def resumo_itens(self, obj):
        itens = obj.carrinho.itens.all()
        html = '<div style="background: #f8f9fa; color:black; padding: 15px; border-radius: 5px; max-height: 300px; overflow-y: auto;">'
        
        for item in itens:
            html += f"""
            <div style="font-size: 20px; color:black; border-bottom: 1px solid #dee2e6; padding: 10px 0; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <strong style="color: black;">{item.produto.nome}</strong><br>
                        <small style="font-size: 18px; color:black;">SKU: {getattr(item.produto, 'sku', 'N/A')}</small>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: #007bff; color: black; padding: 2px 8px; border-radius: 12px; font-size: 18px;">
                            {item.quantidade}x
                        </span><br>
                        <small style="font-size: 18px; color: black;">KZ{item.subtotal:.2f}</small>
                    </div>
                </div>
                <div style="font-size: 17px; color: #28a745; margin-top: 5px;">
                    KZ{item.produto.preco:.2f} cada
                </div>
            </div>
            """
        
        html += f"""
        <div style="font-size: 20px; margin-top: 15px; padding-top: 15px; border-top: 2px solid #007bff; background: white; padding: 10px; border-radius: 4px;">
            <div style="display: flex; justify-content: space-between; font-weight: bold;">
                <span>Total de itens:</span>
                <span style="color: #007bff;">{obj.carrinho.total_itens}</span>
            </div>
        </div>
        """
        html += '</div>'
        return mark_safe(html)
    resumo_itens.short_description = 'Itens do Pedido (Resumo)'

    def lista_itens_detalhada(self, obj):
        itens = obj.carrinho.itens.all().select_related('produto')
        html = '''
        <div style="font-size: 20px; background: white; color:black; border: 1px solid #dee2e6; border-radius: 5px; overflow: hidden;">
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <thead style="background: #343a40; color: white;">
                    <tr>
                        <th style="padding: 17px; text-align: left; border-bottom: 1px solid #454d55;">Produto</th>
                        <th style="padding: 17px; text-align: center; border-bottom: 1px solid #454d55;">Qtd</th>
                        <th style="padding: 17px; text-align: right; border-bottom: 1px solid #454d55;">Preço Unit.</th>
                        <th style="padding: 17px; text-align: right; border-bottom: 1px solid #454d55;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for i, item in enumerate(itens):
            row_bg = '#f8f9fa' if i % 2 == 0 else 'white'
            html += f'''
            <tr style="background: {row_bg};">
                <td style="font-size: 17px;padding: 10px; border-bottom: 1px solid #dee2e6;">
                    <strong>{item.produto.nome}</strong>
                    <br><small style="color: #6c757d;">ID: {item.produto.id}</small>
                </td>
                <td style="padding: 10px; text-align: center; border-bottom: 1px solid #dee2e6;">
                    <span style="background: #6c757d; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">
                        {item.quantidade}
                    </span>
                </td>
                <td style="font-size: 17px; padding: 10px; text-align: right; border-bottom: 1px solid #dee2e6;">
                    KZ{item.produto.preco:.2f}
                </td>
                <td style="font-size: 17px; padding: 10px; text-align: right; border-bottom: 1px solid #dee2e6;">
                    <strong>KZ{item.subtotal:.2f}</strong>
                </td>
            </tr>
            '''
        
        # Linhas de totais
        html += f'''
                </tbody>
                <tfoot>
                    <tr style="font-size: 20px; background: #e9ecef;">
                        <td colspan="2" style="padding: 12px; border-top: 2px solid #dee2e6;"></td>
                        <td style="font-size: 20px; padding: 12px; text-align: right; border-top: 2px solid #dee2e6;">
                            <strong>Subtotal:</strong>
                        </td>
                        <td style="font-size: 20px; padding: 12px; text-align: right; border-top: 2px solid #dee2e6;">
                            <strong>€{obj.carrinho.subtotal:.2f}</strong>
                        </td>
                    </tr>
                    <tr style="background: #e9ecef;">
                        <td colspan="2" style="padding: 12px;"></td>
                        <td style="font-size: 20px; padding: 12px; text-align: right;">
                            <strong>Taxa de Entrega:</strong>
                        </td>
                        <td style="font-size: 20px; padding: 12px; text-align: right;">
                            <strong>KZ{obj.carrinho.taxa_entrega:.2f}</strong>
                        </td>
                    </tr>
                    <tr style="background: #28a745; color: white;">
                        <td colspan="2" style="padding: 15px; border-top: 2px solid #1e7e34;"></td>
                        <td style="font-size: 20px; padding: 15px; text-align: right; border-top: 2px solid #1e7e34;">
                            <strong style="font-size: 16px;">TOTAL:</strong>
                        </td>
                        <td style="font-size: 20px; padding: 15px; text-align: right; border-top: 2px solid #1e7e34;">
                            <strong style="font-size: 16px;">KZ{obj.carrinho.total:.2f}</strong>
                        </td>
                    </tr>
                </tfoot>
            </table>
        </div>
        '''
        return mark_safe(html)
    lista_itens_detalhada.short_description = 'Itens do Pedido (Detalhado)'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'carrinho__usuario'
        ).prefetch_related(
            'carrinho__itens__produto'
        )
    
    actions = ['marcar_como_notificado', 'marcar_como_entregue']
    
    def marcar_como_notificado(self, request, queryset):
        updated = queryset.update(notificado_admin=True)
        self.message_user(request, f'{updated} pedido(s) marcado(s) como notificado(s).')
    marcar_como_notificado.short_description = "Marcar como notificado"
    
    def marcar_como_entregue(self, request, queryset):
        updated = queryset.update(estado='entregue')
        self.message_user(request, f'{updated} pedido(s) marcado(s) como entregue(s).')
    marcar_como_entregue.short_description = "Marcar como entregue"