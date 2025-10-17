from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Autenticação
    path('registro/', views.registro_usuario, name='registro'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),
    
    # Área logada
    path('dashboard/', views.dashboard, name='dashboard'),
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/avatar/upload/', views.upload_avatar, name='upload_avatar'),
    path('perfil/avatar/remover/', views.remover_avatar, name='remover_avatar'),
    path('perfil/excluir/', views.excluir_conta, name='excluir_conta'),
    
    # API
    path('get-municipios/', views.get_municipios, name='get_municipios'),
    
    # Password reset (opcional)
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='nova_senha/password_reset.html'), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='nova_senha/password_reset_done.html'), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='nova_senha/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='nova_senha/password_reset_complete.html'), 
         name='password_reset_complete'),
]