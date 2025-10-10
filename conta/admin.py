from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Usuario

@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    # List view
    list_display = ('email', 'username', 'nome', 'telemovel', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'data_criacao')
    search_fields = ('email', 'username', 'nome', 'cpf')
    ordering = ('email',)
    readonly_fields = ('last_login', 'date_joined', 'data_criacao', 'data_atualizacao')
    
    # Form view - EDITAR
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Informações Pessoais'), {
            'fields': ('nome', 'telemovel', 'cpf', 'data_nascimento', 'foto_perfil')
        }),
        (_('Endereço'), {
            'fields': ('bairro', 'cidade', 'provincia', 'municipio')
        }),
        (_('Permissões'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Datas Importantes'), {
            'fields': ('last_login', 'date_joined', 'data_criacao', 'data_atualizacao')
        }),
    )

    # Add form - CRIAR
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'nome', 'cpf', 'password1', 'password2'),
        }),
    )
    
    # Filter horizontal
    filter_horizontal = ('groups', 'user_permissions',)