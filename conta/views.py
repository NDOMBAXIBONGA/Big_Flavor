from carinho.models import PedidoEntrega
from django.utils import timezone
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash, get_user_model
from django.contrib import messages
import os

from .forms import RegistroUsuarioForm, LoginForm, EditarPerfilForm, AvatarForm

User = get_user_model()

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
    
    # Últimos pedidos do usuário (últimos 5 pedidos)
    ultimos_pedidos = PedidoEntrega.objects.filter(
        carrinho__usuario=usuario
    ).select_related('carrinho').prefetch_related('carrinho__itens__produto').order_by('-data_solicitacao')[:3]
    
    # Estatísticas do usuário
    total_pedidos = PedidoEntrega.objects.filter(
        carrinho__usuario=usuario
    ).count()
    
    pedidos_entregues = PedidoEntrega.objects.filter(
        carrinho__usuario=usuario,
        estado='entregue'
    ).count()
    
    # Calcular total gasto
    total_gasto = 0
    for pedido in ultimos_pedidos:
        if hasattr(pedido.carrinho, 'total'):
            total_gasto += pedido.carrinho.total
        else:
            # Fallback: calcular manualmente
            total_gasto += sum(item.subtotal for item in pedido.carrinho.itens.all())
    
    context = {
        'usuario': usuario,  # Já inclui o usuário aqui
        'ultimos_pedidos': ultimos_pedidos,
        'total_pedidos': total_pedidos,
        'pedidos_entregues': pedidos_entregues,
        'total_gasto': total_gasto,
    }
    
    return render(request, 'perfil.html', context)  # Remove o segundo dicionário

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

def get_municipios(request):
        """View para retornar municípios baseados na província selecionada"""
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                provincia_id = data.get('provincia_id')
                
                form = RegistroUsuarioForm()
                municipios_data = form.MUNICIPIOS_POR_PROVINCIA.get(provincia_id, [])
                
                # Converter para o formato esperado pelo JavaScript
                municipios = [{'id': code, 'nome': name} for code, name in municipios_data if code]  # Filtra opção vazia
                
                return JsonResponse({'municipios': municipios})
                
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Dados inválidos'}, status=400)
            except Exception as e:
                return JsonResponse({'error': f'Erro interno: {str(e)}'}, status=500)
        
        return JsonResponse({'error': 'Método não permitido'}, status=405)