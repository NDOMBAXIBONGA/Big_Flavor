# seu_app/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

# Admin básico sem fieldsets complexos
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'nome', 'telemovel', 'cpf', 'data_nascimento', 'bairro', 'cidade', 'provincia', 'municipio', 'is_staff', 'is_active', 'data_criacao')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'nome')
    ordering = ('email',)
    readonly_fields = ('data_criacao', 'data_atualizacao', 'last_login')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('nome', 'telemovel', 'cpf', 'data_nascimento', 'bairro', 'cidade', 'provincia', 'municipio')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Datas', {'fields': ('last_login', 'data_criacao', 'data_atualizacao')}),
    )

admin.site.register(Usuario, CustomUserAdmin)