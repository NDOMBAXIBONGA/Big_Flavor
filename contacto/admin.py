from django.contrib import admin
from .models import Contacto

@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email', 'assunto', 'data_envio', 'lido']
    list_filter = ['assunto', 'lido', 'data_envio']
    search_fields = ['nome', 'email', 'mensagem']
    readonly_fields = ['data_envio']
    list_per_page = 20
    
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('nome', 'email', 'telemovel')
        }),
        ('Mensagem', {
            'fields': ('assunto', 'mensagem')
        }),
        ('Metadados', {
            'fields': ('data_envio', 'lido'),
            'classes': ('collapse',)
        }),
    )