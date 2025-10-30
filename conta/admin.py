from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Usuario

@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'nome', 'telemovel', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'data_criacao')
    search_fields = ('email', 'nome')
    ordering = ('email',)
    readonly_fields = ('data_criacao', 'data_atualizacao', 'last_login', 'date_joined')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Informações Pessoais'), {
            'fields': ('nome', 'telemovel', 'foto_perfil')
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

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nome', 'password1', 'password2'),
        }),
    )
    
    filter_horizontal = ('groups', 'user_permissions',)