# balanco/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import RelatorioBalanco

@admin.register(RelatorioBalanco)
class RelatorioBalancoAdmin(admin.ModelAdmin):
    list_display = [
        'nome_relatorio',
        'periodo_relatorio',
        'total_pedidos_periodo',
        'total_pedidos_entregues',
        'total_pedidos_cancelados',
        'subtotal_pedidos',
        'valor_total_cancelados',
        'total_geral',
        'taxa_sucesso_display',
        'taxa_cancelamento_display',
        'data_criacao',
        'acoes_personalizadas'
    ]
    
    list_filter = [
        'data_inicio',
        'data_fim',
        'data_criacao'
    ]
    
    search_fields = [
        'nome_relatorio'
    ]
    
    readonly_fields = [
        'total_pedidos_entregues',
        'total_pedidos_cancelados',
        'subtotal_pedidos',
        'valor_total_cancelados',
        'total_geral',
        'total_pedidos_periodo',
        'data_criacao',
        'data_atualizacao',
        'taxa_sucesso_display',
        'taxa_cancelamento_display',
        'taxa_cancelamento_valor_display',
        'valor_medio_entrega_display',
        'valor_medio_pedido_display',
        'eficiencia_operacional_display',
        'dias_periodo_display',
        'pedidos_por_dia_display',
        'subtotal_por_dia_display',
        'valor_geral_por_dia_display',
        'botao_atualizar_dados'  # NOVO CAMPO READONLY
    ]
    
    fieldsets = (
        ('Configuração do Relatório', {
            'fields': (
                'nome_relatorio',
                'data_inicio',
                'data_fim',
                'botao_atualizar_dados'  # BOTÃO ADICIONADO AQUI
            )
        }),
        ('Estatísticas de Pedidos', {
            'fields': (
                'total_pedidos_periodo',
                'total_pedidos_entregues',
                'total_pedidos_cancelados',
                'taxa_sucesso_display',
                'taxa_cancelamento_display',
                'dias_periodo_display',
                'pedidos_por_dia_display'
            )
        }),
        ('Estatísticas Financeiras - Detalhadas', {
            'fields': (
                'subtotal_pedidos',
                'valor_total_cancelados',
                'total_geral',
                'taxa_cancelamento_valor_display',
                'valor_medio_entrega_display',
                'valor_medio_pedido_display',
                'eficiencia_operacional_display',
                'subtotal_por_dia_display',
                'valor_geral_por_dia_display'
            )
        }),
        ('Metadados', {
            'fields': (
                'data_criacao',
                'data_atualizacao'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['atualizar_dados_relatorios', 'criar_relatorio_mensal', 'criar_relatorio_semanal']  # NOVAS AÇÕES
    
    # NOVO: Botão de atualizar dados na página de edição
    def botao_atualizar_dados(self, obj):
        if obj.pk:
            return format_html(
                '<a href="{}" class="button" style="background-color: #417690; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; font-weight: bold;">'
                '🔄 Atualizar Dados Agora'
                '</a>'
                '&nbsp;&nbsp;'
                '<span style="color: #666; font-size: 12px;">Clique para buscar os dados mais recentes</span>',
                reverse('admin:balanco_relatoriobalanco_atualizar', args=[obj.pk])
            )
        return "Salve o relatório primeiro para poder atualizar os dados."
    botao_atualizar_dados.short_description = 'Atualização de Dados'
    
    # Métodos para display na lista
    def periodo_relatorio(self, obj):
        return f"{obj.data_inicio} a {obj.data_fim}"
    periodo_relatorio.short_description = 'Período'
    
    def taxa_sucesso_display(self, obj):
        return f"{obj.taxa_sucesso:.1f}%"
    taxa_sucesso_display.short_description = 'Taxa de Sucesso'
    
    def taxa_cancelamento_display(self, obj):
        return f"{obj.taxa_cancelamento:.1f}%"
    taxa_cancelamento_display.short_description = 'Taxa de Cancelamento (Qtd)'
    
    def taxa_cancelamento_valor_display(self, obj):
        return f"{obj.taxa_cancelamento_valor:.1f}%"
    taxa_cancelamento_valor_display.short_description = 'Taxa de Cancelamento (Valor)'
    
    def valor_medio_entrega_display(self, obj):
        return f"R$ {obj.valor_medio_entrega:.2f}"
    valor_medio_entrega_display.short_description = 'Valor Médio por Entrega'
    
    def valor_medio_pedido_display(self, obj):
        return f"R$ {obj.valor_medio_pedido:.2f}"
    valor_medio_pedido_display.short_description = 'Valor Médio por Pedido'
    
    def eficiencia_operacional_display(self, obj):
        return f"{obj.eficiencia_operacional:.1f}%"
    eficiencia_operacional_display.short_description = 'Eficiência Operacional'
    
    def dias_periodo_display(self, obj):
        return f"{obj.dias_periodo} dias"
    dias_periodo_display.short_description = 'Dias no Período'
    
    def pedidos_por_dia_display(self, obj):
        return f"{obj.pedidos_por_dia:.1f}"
    pedidos_por_dia_display.short_description = 'Pedidos por Dia'
    
    def subtotal_por_dia_display(self, obj):
        return f"R$ {obj.subtotal_por_dia:.2f}"
    subtotal_por_dia_display.short_description = 'Subtotal por Dia'
    
    def valor_geral_por_dia_display(self, obj):
        return f"R$ {obj.valor_geral_por_dia:.2f}"
    valor_geral_por_dia_display.short_description = 'Total Geral por Dia'
    
    def acoes_personalizadas(self, obj):
        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<a class="button" href="{}" style="background-color: #417690; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px;">'
            '🔄 Atualizar'
            '</a>'
            '<a class="button" href="{}" style="background-color: #4CAF50; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px;">'
            '👁️ Visualizar'
            '</a>'
            '<a class="button" href="{}" style="background-color: #FF9800; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px;">'
            '✏️ Editar'
            '</a>'
            '</div>',
            reverse('admin:balanco_relatoriobalanco_atualizar', args=[obj.pk]),
            reverse('admin:balanco_relatoriobalanco_change', args=[obj.pk]),
            reverse('admin:balanco_relatoriobalanco_change', args=[obj.pk])
        )
    acoes_personalizadas.short_description = 'Ações'
    
    # AÇÃO: Atualizar dados dos relatórios selecionados
    def atualizar_dados_relatorios(self, request, queryset):
        relatorios_atualizados = 0
        for relatorio in queryset:
            try:
                relatorio.buscar_dados_carrinho()
                relatorios_atualizados += 1
            except Exception as e:
                self.message_user(
                    request, 
                    f"Erro ao atualizar relatório {relatorio.nome_relatorio}: {str(e)}", 
                    level=messages.ERROR
                )
        
        if relatorios_atualizados > 0:
            self.message_user(
                request, 
                f"✅ Dados de {relatorios_atualizados} relatório(s) atualizados com sucesso!", 
                level=messages.SUCCESS
            )
    atualizar_dados_relatorios.short_description = "🔄 Atualizar dados dos relatórios selecionados"
    
    # NOVA AÇÃO: Criar relatório mensal automático
    def criar_relatorio_mensal(self, request, queryset):
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        # Define início e fim do mês atual
        hoje = timezone.now().date()
        primeiro_dia_mes = hoje.replace(day=1)
        ultimo_dia_mes = (primeiro_dia_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Verifica se já existe relatório para este mês
        relatorio_existente = RelatorioBalanco.objects.filter(
            data_inicio=primeiro_dia_mes,
            data_fim=ultimo_dia_mes
        ).exists()
        
        if relatorio_existente:
            self.message_user(
                request, 
                "⚠️ Já existe um relatório mensal para este mês!", 
                level=messages.WARNING
            )
            return
        
        # Cria novo relatório mensal
        relatorio = RelatorioBalanco.objects.create(
            nome_relatorio=f"Relatório Mensal - {hoje.strftime('%B %Y')}",
            data_inicio=primeiro_dia_mes,
            data_fim=ultimo_dia_mes
        )
        
        relatorio.buscar_dados_carrinho()
        
        self.message_user(
            request, 
            f"✅ Relatório mensal criado com sucesso! Dados atualizados automaticamente.", 
            level=messages.SUCCESS
        )
    
    criar_relatorio_mensal.short_description = "📅 Criar relatório mensal automático"
    
    # NOVA AÇÃO: Criar relatório semanal automático
    def criar_relatorio_semanal(self, request, queryset):
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        # Define início e fim da semana atual (segunda a domingo)
        hoje = timezone.now().date()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + timedelta(days=6)
        
        # Verifica se já existe relatório para esta semana
        relatorio_existente = RelatorioBalanco.objects.filter(
            data_inicio=inicio_semana,
            data_fim=fim_semana
        ).exists()
        
        if relatorio_existente:
            self.message_user(
                request, 
                "⚠️ Já existe um relatório semanal para esta semana!", 
                level=messages.WARNING
            )
            return
        
        # Cria novo relatório semanal
        relatorio = RelatorioBalanco.objects.create(
            nome_relatorio=f"Relatório Semanal - {inicio_semana.strftime('%d/%m')} a {fim_semana.strftime('%d/%m/%Y')}",
            data_inicio=inicio_semana,
            data_fim=fim_semana
        )
        
        relatorio.buscar_dados_carrinho()
        
        self.message_user(
            request, 
            f"✅ Relatório semanal criado com sucesso! Dados atualizados automaticamente.", 
            level=messages.SUCCESS
        )
    
    criar_relatorio_semanal.short_description = "📊 Criar relatório semanal automático"
    
    # URL personalizada para atualizar um relatório específico
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/atualizar/',
                self.admin_site.admin_view(self.atualizar_relatorio),
                name='balanco_relatoriobalanco_atualizar',
            ),
            path(
                'criar-mensal/',
                self.admin_site.admin_view(self.criar_relatorio_mensal_direto),
                name='balanco_relatoriobalanco_criar_mensal',
            ),
            path(
                'criar-semanal/',
                self.admin_site.admin_view(self.criar_relatorio_semanal_direto),
                name='balanco_relatoriobalanco_criar_semanal',
            ),
        ]
        return custom_urls + urls
    
    def atualizar_relatorio(self, request, object_id, *args, **kwargs):
        """View personalizada para atualizar um relatório específico"""
        try:
            relatorio = RelatorioBalanco.objects.get(pk=object_id)
            relatorio.buscar_dados_carrinho()
            self.message_user(
                request, 
                f"✅ Relatório '{relatorio.nome_relatorio}' atualizado com sucesso!", 
                level=messages.SUCCESS
            )
        except RelatorioBalanco.DoesNotExist:
            self.message_user(request, "❌ Relatório não encontrado!", level=messages.ERROR)
        
        return HttpResponseRedirect(
            reverse('admin:balanco_relatoriobalanco_change', args=[object_id])
        )
    
    # Views para criar relatórios diretamente pela URL
    def criar_relatorio_mensal_direto(self, request):
        self.criar_relatorio_mensal(request, RelatorioBalanco.objects.none())
        return HttpResponseRedirect(reverse('admin:balanco_relatoriobalanco_changelist'))
    
    def criar_relatorio_semanal_direto(self, request):
        self.criar_relatorio_semanal(request, RelatorioBalanco.objects.none())
        return HttpResponseRedirect(reverse('admin:balanco_relatoriobalanco_changelist'))
    
    # Customização do changelist para adicionar botões extras
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['botoes_extras'] = True
        return super().changelist_view(request, extra_context=extra_context)
    
    # Sobrescrevendo o template para adicionar botões personalizados
    def changeform_template(self, obj=None):
        if obj:
            return 'admin/balanco/relatoriobalanco/change_form.html'
        return super().changeform_template(obj)
    
    # Sobrescrevendo o save para garantir que os dados sejam buscados ao criar
    def save_model(self, request, obj, form, change):
        if not change:  # Se for um novo objeto
            super().save_model(request, obj, form, change)
            obj.buscar_dados_carrinho()
        else:
            super().save_model(request, obj, form, change)
    
    # Customização do formulário de adição
    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().add_view(request, form_url, extra_context)
    
    # Ordenação padrão
    ordering = ['-data_criacao']
    
    # Configuração de listas por página
    list_per_page = 20
    
    # Campos que podem ser clicados para editar
    list_display_links = ['nome_relatorio']