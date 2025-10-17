from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash, get_user_model
from django.contrib import messages
from django.http import JsonResponse
import os

from .forms import RegistroUsuarioForm, LoginForm, ContactForm, EditarPerfilForm, AvatarForm
from .models import Usuario

User = get_user_model()

# Views públicas
def contact_page(request):
    contact_form = ContactForm(request.POST or None)
    context = {
        "title": "Contact Page",
        "content": "Bem vindo a Contact Page",
        "form": contact_form	
    }
    if contact_form.is_valid():
        print(contact_form.cleaned_data)
    return render(request, "contact/view.html", context)

def registro_usuario(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            try:
                usuario = form.save()
                usuario = authenticate(
                    request,
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['senha']
                )
                
                if usuario is not None:
                    login(request, usuario)
                    messages.success(request, f'Bem-vindo(a), {usuario.nome}!')
                    return redirect('dashboard')
                else:
                    messages.success(request, 'Registro realizado! Faça login para continuar.')
                    return redirect('login')
                    
            except Exception as e:
                messages.error(request, f'Erro no registro: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registro.html', {'form': form})

def login_usuario(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            usuario = authenticate(request, email=email, password=password)
            
            if usuario is not None:
                login(request, usuario)
                messages.success(request, f'Bem-vindo de volta, {usuario.nome}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'E-mail ou senha incorretos.')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

def logout_usuario(request):
    logout(request)
    messages.success(request, 'Você saiu da sua conta.')
    return redirect('/')

# Views protegidas
@login_required
def dashboard(request):
    return render(request, 'logado.html', {'usuario': request.user})

@login_required
def perfil(request):
    usuario = request.user
    # Adicione aqui lógica para estatísticas se necessário
    return render(request, 'perfil.html', {'usuario': usuario})

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            
            # Atualizar sessão se a senha foi alterada
            if form.cleaned_data.get('nova_senha'):
                update_session_auth_hash(request, user)
                messages.success(request, 'Perfil e senha alterados com sucesso!')
            else:
                messages.success(request, 'Perfil atualizado com sucesso!')
            
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = EditarPerfilForm(instance=request.user)
    
    return render(request, 'editar_perfil.html', {'form': form})

@login_required
def upload_avatar(request):
    if request.method == 'POST' and request.FILES:
        form = AvatarForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Foto de perfil atualizada com sucesso!')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('perfil')

@login_required
def remover_avatar(request):
    if request.method == 'POST':
        user = request.user
        if user.foto_perfil:
            if os.path.isfile(user.foto_perfil.path):
                os.remove(user.foto_perfil.path)
            user.foto_perfil = None
            user.save()
            messages.success(request, 'Foto de perfil removida com sucesso!')
        else:
            messages.info(request, 'Você não possui uma foto de perfil.')
    return redirect('perfil')

@login_required
def excluir_conta(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, 'Sua conta foi excluída com sucesso.')
        return redirect('/')
    return redirect('perfil')