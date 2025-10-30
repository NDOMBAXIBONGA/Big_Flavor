from carinho.models import PedidoEntrega
from django.utils import timezone
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash, get_user_model
from django.contrib import messages
from django.db.models import Count
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from functools import wraps
import os

from .forms import RegistroUsuarioForm, LoginForm, EditarPerfilForm, AvatarForm

User = get_user_model()

# Cache decorator personalizado para dados de usuário
def cache_dados_usuario(timeout):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            from django.core.cache import cache
            if request.user.is_authenticated:
                cache_key = f"user_{request.user.id}_{view_func.__name__}"
            else:
                cache_key = f"anon_{view_func.__name__}_{request.path}"
            
            response = cache.get(cache_key)
            
            if response is None:
                response = view_func(request, *args, **kwargs)
                cache.set(cache_key, response, timeout)
            
            return response
        return _wrapped_view
    return decorator

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

# Views protegidas com cache
@login_required
@cache_page(60 * 10)  # 10 minutos de cache
@vary_on_cookie  # Diferencia por usuário
def dashboard(request):
    return render(request, 'logado.html', {'usuario': request.user})

@login_required
@cache_page(60 * 15)  # 15 minutos de cache para perfil
@vary_on_cookie
def perfil(request):
    usuario = request.user
    
    # Cache específico para dados do perfil
    from django.core.cache import cache
    cache_key = f"perfil_data_user_{usuario.id}"
    perfil_data = cache.get(cache_key)
    
    if perfil_data is None:
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
        
        perfil_data = {
            'ultimos_pedidos': ultimos_pedidos,
            'total_pedidos': total_pedidos,
            'pedidos_entregues': pedidos_entregues,
            'total_gasto': total_gasto,
        }
        
        # Cache por 15 minutos
        cache.set(cache_key, perfil_data, 60 * 15)
    
    context = {
        'usuario': usuario,
        **perfil_data
    }
    
    return render(request, 'perfil.html', context)

# SEM CACHE - operações de escrita
@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            
            # Invalidar cache do perfil
            invalidar_cache_perfil(request.user)
            
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

# SEM CACHE - operações de escrita
@login_required
def upload_avatar(request):
    if request.method == 'POST' and request.FILES:
        form = AvatarForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            
            # Invalidar cache do perfil
            invalidar_cache_perfil(request.user)
            
            messages.success(request, 'Foto de perfil atualizada com sucesso!')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('perfil')

# SEM CACHE - operações de escrita
@login_required
def remover_avatar(request):
    if request.method == 'POST':
        user = request.user
        if user.foto_perfil:
            if os.path.isfile(user.foto_perfil.path):
                os.remove(user.foto_perfil.path)
            user.foto_perfil = None
            user.save()
            
            # Invalidar cache do perfil
            invalidar_cache_perfil(request.user)
            
            messages.success(request, 'Foto de perfil removida com sucesso!')
        else:
            messages.info(request, 'Você não possui uma foto de perfil.')
    return redirect('perfil')

# SEM CACHE - operações de escrita
@login_required
def excluir_conta(request):
    if request.method == 'POST':
        user = request.user
        
        # Invalidar todos os caches do usuário antes de deletar
        invalidar_todos_caches_usuario(user)
        
        user.delete()
        messages.success(request, 'Sua conta foi excluída com sucesso.')
        return redirect('/')
    return redirect('perfil')

# Cache para dados estáticos como municípios - 24 horas
@cache_page(60 * 60 * 24)  # 24 horas
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

# Funções de invalidação de cache
def invalidar_cache_perfil(usuario):
    """Invalida cache específico do perfil do usuário"""
    from django.core.cache import cache
    cache_keys = [
        f"perfil_data_user_{usuario.id}",
        f"perfil_user_{usuario.id}",
        f"dashboard_user_{usuario.id}",
    ]
    for key in cache_keys:
        cache.delete(key)
    print(f"Cache do perfil invalidado para usuário {usuario.id}")

def invalidar_todos_caches_usuario(usuario):
    """Invalida todos os caches relacionados ao usuário"""
    from django.core.cache import cache
    cache_keys = [
        f"perfil_data_user_{usuario.id}",
        f"perfil_user_{usuario.id}", 
        f"dashboard_user_{usuario.id}",
        f"user_{usuario.id}_perfil",
        f"user_{usuario.id}_dashboard",
    ]
    
    # Também invalida cache de pedidos se existir
    try:
        from carinho.views import invalidar_cache_pedidos
        invalidar_cache_pedidos(usuario)
    except ImportError:
        pass
    
    for key in cache_keys:
        cache.delete(key)
    
    print(f"Todos os caches invalidados para usuário {usuario.id}")

# View adicional para estatísticas do usuário com cache
@login_required
@cache_dados_usuario(60 * 30)  # 30 minutos
def estatisticas_usuario(request):
    """View para estatísticas detalhadas do usuário"""
    usuario = request.user
    
    # Dados que podem ser cacheados
    pedidos_ultimo_mes = PedidoEntrega.objects.filter(
        carrinho__usuario=usuario,
        data_solicitacao__gte=timezone.now() - timezone.timedelta(days=30)
    ).count()
    
    produto_favorito = PedidoEntrega.objects.filter(
        carrinho__usuario=usuario
    ).values(
        'carrinho__itens__produto__nome'
    ).annotate(
        total=Count('carrinho__itens__produto')
    ).order_by('-total').first()
    
    context = {
        'usuario': usuario,
        'pedidos_ultimo_mes': pedidos_ultimo_mes,
        'produto_favorito': produto_favorito,
    }
    
    return render(request, 'estatisticas_usuario.html', context)

# API para dados do usuário com cache
@login_required
@cache_page(60 * 5)  # 5 minutos para API
def api_dados_usuario(request):
    """API para dados do usuário (para AJAX)"""
    usuario = request.user
    
    dados = {
        'nome': usuario.nome,
        'email': usuario.email,
        'telemovel': usuario.telemovel,
        'membro_desde': usuario.date_joined.strftime('%d/%m/%Y'),
        'total_pedidos': PedidoEntrega.objects.filter(carrinho__usuario=usuario).count(),
    }
    
    return JsonResponse(dados)