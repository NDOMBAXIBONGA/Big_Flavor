from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Usuario

@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'nome', 'telemovel', 'cpf', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'data_criacao', 'cidade')
    search_fields = ('email', 'username', 'nome', 'cpf', 'telemovel')
    ordering = ('email',)
    readonly_fields = ('data_criacao', 'data_atualizacao', 'last_login', 'date_joined')
    
    # Fieldsets corretos para AbstractUser
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Informações Pessoais'), {
            'fields': ('nome', 'telemovel', 'cpf', 'data_nascimento', 'foto_perfil')
        }),
        (_('Endereço'), {
            'fields': ('bairro', 'cidade', 'provincia', 'municipio')
        }),
        (_('Permissões'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Datas Importantes'), {
            'fields': ('last_login', 'date_joined', 'data_criacao', 'data_atualizacao')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'nome', 'cpf', 'password1', 'password2', 'telemovel', 'data_nascimento'),
        }),
    )
    
    # Agora filter_horizontal funcionará
    filter_horizontal = ('groups', 'user_permissions',)