from django.contrib import admin
from .models import Produto

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'categoria', 'preco', 'estoque', 'status', 'data_criacao']
    list_filter = ['categoria', 'status', 'data_criacao']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['data_criacao', 'data_atualizacao']
    list_editable = ['estoque', 'status']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao_curta', 'descricao', 'categoria')
        }),
        ('Preço e Estoque', {
            'fields': ('preco', 'estoque')
        }),
        ('Imagem e Status', {
            'fields': ('imagem', 'status')
        }),
        ('Metadados', {
            'fields': ('data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )