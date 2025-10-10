from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class CustomUserAdmin(UserAdmin):  # ← Corrigido: herda de UserAdmin
    list_display = ('email', 'nome', 'telemovel', 'cpf', 'data_nascimento', 'bairro', 'cidade', 'provincia', 'municipio', 'is_staff', 'is_active', 'data_criacao')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'nome')
    ordering = ('email',)
    readonly_fields = ('data_criacao', 'data_atualizacao', 'last_login')
    
    # Fieldsets devem incluir campos base do User
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('nome', 'telemovel', 'cpf', 'data_nascimento', 'bairro', 'cidade', 'provincia', 'municipio')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas', {'fields': ('last_login', 'data_criacao', 'data_atualizacao')}),
    )
    
    # IMPORTANTE: Definir add_fieldsets para formulário de criação
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'nome', 'telemovel', 'cpf', 'data_nascimento'),
        }),
    )

admin.site.register(Usuario, CustomUserAdmin)