from .forms import EditarPerfilForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .forms import RegistroUsuarioForm, LoginForm, ContactForm, AvatarForm
from .models import Usuario
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model, logout, update_session_auth_hash

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

#def login_page(request):
#    form = LoginForm(request.POST or None)
#    context = {
#                    "form": form
#              }
#    print("User logado")
#    #print(request.user.is_authenticated)
#    if form.is_valid():
#        print(form.cleaned_data)
#        username = form.cleaned_data.get("username")
#        password = form.cleaned_data.get("password")
#        user = authenticate(request, username=username, password=password) 
#        print(user)
#        #print(request.user.is_authenticated)
#        if user is not None:
#            #print(request.user.is_authenticated)
#            login(request, user)
#            print("Login válido")
#            # Redireciona para uma página de sucesso.
#            return redirect("/")
#        else:
#            #Retorna uma mensagem de erro de 'invalid login'.
#            print("Login inválido")
#    return render(request, "login.html", context)

User = get_user_model()

#def register_page(request):
#    form = RegisterForm(request.POST or None)
#    context = {
#                    "form": form
#              }
#    if form.is_valid():
#        print(form.cleaned_data)
#        username = form.cleaned_data.get("username")
#        email = form.cleaned_data.get("email")
#        password = form.cleaned_data.get("password")
#        new_user = User.objects.create_user(username, email, password)
#        print(new_user)
#    return render(request, "register.html", context)

def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            try:
                # Salvar o usuário
                usuario = form.save()
                
                # Autenticar e fazer login automaticamente
                usuario = authenticate(
                    request,
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['senha']
                )
                
                if usuario is not None:
                    login(request, usuario)
                    messages.success(request, f'Bem-vindo(a), {usuario.nome}!')
                    return redirect('/')
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
                
                # Redirecionar para próxima página ou dashboard
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'E-mail ou senha incorretos.')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

@login_required
def logout_usuario(request):
    logout(request)
    return redirect('/')

@login_required
def dashboard(request):
    return render(request, 'logado.html', {'usuario': request.user})

@login_required
def perfil(request):
    usuario = request.user
    return render(request, 'perfil.html', {'usuario': usuario})

# API para municípios (opcional)
def get_municipios(request):
    provincia = request.GET.get('provincia')
    municipios = {
        'luanda': [{'id': 'belas', 'nome': 'Belas'}, ...],
        'benguela': [{'id': 'benguela', 'nome': 'Benguela'}, ...],
        # ... outras províncias
    }
    return JsonResponse(municipios.get(provincia, []), safe=False)


@login_required
def minha_view_protegida(request):
    # Esta view só pode ser acessada por usuários logados
    return render(request, 'protegida.html')

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, user_instance=request.user)
        
        if form.is_valid():
            dados = form.cleaned_data
            
            # Atualizar dados do usuário
            request.user.nome = dados['nome']
            request.user.email = dados['email']
            request.user.telemovel = dados['telemovel']
            request.user.data_nascimento = dados['data_nascimento']
            request.user.bairro = dados['bairro']
            request.user.cidade = dados['cidade']
            request.user.provincia = dados['provincia']
            request.user.municipio = dados['municipio']
            request.user.save()
            
            # Processar alteração de senha
            nova_senha = dados.get('nova_senha')
            senha_atual = dados.get('senha_atual')
            
            if nova_senha and senha_atual:
                if request.user.check_password(senha_atual):
                    request.user.set_password(nova_senha)
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    messages.success(request, 'Perfil e senha alterados com sucesso!')
                else:
                    messages.error(request, 'Senha atual incorreta. O perfil foi atualizado, mas a senha não foi alterada.')
            else:
                messages.success(request, 'Perfil atualizado com sucesso!')
            
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = EditarPerfilForm(user_instance=request.user)
    
    return render(request, 'editar_perfil.html', {'form': form})

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django.contrib import messages
from carinho.models import PedidoEntrega  # Import do seu modelo
import os

@login_required
def perfil(request):
    User = get_user_model()
    usuario = request.user
    
    try:
        # Buscar pedidos do usuário atual
        pedidos_usuario = PedidoEntrega.objects.filter(usuario=usuario)
        
        # Estatísticas básicas
        total_pedidos = pedidos_usuario.count()
        
        # Ajuste o campo de estado conforme seu modelo
        # Se não tiver campo 'entregue', use outro critério ou remova
        pedidos_entregues = pedidos_usuario.filter(estado='entregue').count()
        
        # Calcular total gasto - ajuste o campo de preço conforme seu modelo
        # Se não tiver campo 'total', calcule baseado nos itens
        total_gasto_result = pedidos_usuario.aggregate(
            total=Sum('total')
        )['total'] or 0
        
        # Últimos pedidos
        ultimos_pedidos = pedidos_usuario.order_by('-data_criacao')[:5]
        
    except Exception as e:
        print(f"Erro ao buscar estatísticas: {e}")
        # Fallback seguro
        total_pedidos = 0
        pedidos_entregues = 0
        total_gasto_result = 0
        ultimos_pedidos = []

    context = {
        'usuario': usuario,
        'total_pedidos': total_pedidos,
        'pedidos_entregues': pedidos_entregues,
        'total_gasto': total_gasto_result,
        'ultimos_pedidos': ultimos_pedidos
    }
    return render(request, 'perfil.html', context)

@login_required
def upload_avatar(request):
    if request.method == 'POST' and request.FILES:
        # Usando o formulário simplificado sem ModelForm
        foto_perfil = request.FILES.get('foto_perfil')
        
        if foto_perfil:
            # Validações básicas
            max_size = 5 * 1024 * 1024  # 5MB
            if foto_perfil.size > max_size:
                messages.error(request, 'A imagem deve ter no máximo 5MB.')
                return redirect('perfil')
            
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            import os
            ext = os.path.splitext(foto_perfil.name)[1].lower()
            if ext not in valid_extensions:
                messages.error(request, 'Formato não suportado. Use JPG, PNG ou GIF.')
                return redirect('perfil')
            
            # Salvar a imagem
            user = request.user
            user.foto_perfil = foto_perfil
            user.save()
            messages.success(request, 'Foto de perfil atualizada com sucesso!')
        else:
            messages.error(request, 'Nenhuma imagem foi selecionada.')
    
    return redirect('perfil')

@login_required
def remover_avatar(request):
    if request.method == 'POST':
        user = request.user
        if user.foto_perfil:
            # Deletar arquivo físico se existir
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
        return redirect('index')
    return redirect('perfil')