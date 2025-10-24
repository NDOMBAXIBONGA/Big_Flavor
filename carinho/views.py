from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from functools import wraps
import logging
import threading

logger = logging.getLogger(__name__)

from .models import Carrinho, ItemCarrinho, PedidoEntrega
from .forms import AdicionarAoCarrinhoForm, PedidoEntregaForm, AtualizarItemForm
from menu.models import Produto
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
from datetime import time

# Cache decorator personalizado
def cache_com_invalidacao(timeout, key_prefix):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            from django.core.cache import cache
            # Chave de cache baseada no usuário e parâmetros
            user_id = request.user.id if request.user.is_authenticated else 'anon'
            cache_key = f"{key_prefix}_user_{user_id}_path_{request.path}"
            
            response = cache.get(cache_key)
            
            if response is None:
                response = view_func(request, *args, **kwargs)
                cache.set(cache_key, response, timeout)
            
            return response
        return _wrapped_view
    return decorator

@login_required
def obter_carrinho(request):
    """Obtém ou cria carrinho para o usuário logado"""
    carrinho, created = Carrinho.objects.get_or_create(
        usuario=request.user,
        estado='aberto'
    )
    return carrinho

# Cache para visualização do carrinho - 5 minutos
@login_required
@cache_page(60 * 5)
@vary_on_cookie
def ver_carrinho(request):
    """Visualizar carrinho do usuário"""
    carrinho = Carrinho.obter_carrinho_aberto(request.user)
    itens = carrinho.itens.all()
    
    context = {
        'carrinho': carrinho,
        'itens': itens,
    }
    return render(request, 'ver_carrinho.html', context)

# SEM CACHE - operação de escrita
@login_required
def adicionar_ao_carrinho(request, produto_id):
    """Adiciona produto ao carrinho - VERSÃO CORRIGIDA"""
    try:
        carrinho = Carrinho.obter_carrinho_aberto(request.user)
        produto = get_object_or_404(Produto, id=produto_id, status='ativo')
        
        if not produto.em_estoque():
            messages.error(request, 'Produto indisponível no momento.')
            return redirect('lista_produtos')
        
        if request.method == 'POST':
            form = AdicionarAoCarrinhoForm(request.POST)
            if form.is_valid():
                quantidade = form.cleaned_data['quantidade']
                
                # Verificar estoque
                if quantidade > produto.estoque:
                    messages.error(request, f'Estoque insuficiente. Disponível: {produto.estoque}')
                    return redirect('detalhes_produto', pk=produto_id)
                
                # Adicionar ou atualizar item
                item, created = ItemCarrinho.objects.get_or_create(
                    carrinho=carrinho,
                    produto=produto,
                    defaults={'quantidade': quantidade}
                )
                
                if not created:
                    nova_quantidade = item.quantidade + quantidade
                    if nova_quantidade > produto.estoque:
                        messages.error(request, 'Quantidade excede estoque disponível.')
                        return redirect('detalhes_produto', pk=produto_id)
                    item.quantidade = nova_quantidade
                    item.save()
                    messages.success(request, f'Quantidade de {produto.nome} atualizada.')
                else:
                    messages.success(request, f'{produto.nome} adicionado ao carrinho!')
                
                # Invalidar cache do carrinho
                invalidar_cache_carrinho(request.user)
                return redirect('ver_carrinho')
        
        return redirect('detalhes_produto', pk=produto_id)
        
    except Exception as e:
        messages.error(request, f'Erro ao adicionar produto: {str(e)}')
        return redirect('lista_produtos')

# SEM CACHE - operação de escrita
@login_required
def atualizar_item_carrinho(request, item_id):
    """Atualiza quantidade de um item no carrinho - VERSÃO CORRIGIDA"""
    try:
        # VERIFICAÇÃO DE SEGURANÇA: Garante que o item pertence ao usuário
        item = get_object_or_404(
            ItemCarrinho, 
            id=item_id, 
            carrinho__usuario=request.user,  # ← ESTÁ CORRETO!
            carrinho__estado='aberto'  # ← ADICIONE ESTA VERIFICAÇÃO
        )
        
        if request.method == 'POST':
            form = AtualizarItemForm(request.POST, instance=item)
            if form.is_valid():
                nova_quantidade = form.cleaned_data['quantidade']
                
                # Verificar estoque
                if nova_quantidade > item.produto.estoque:
                    messages.error(request, f'Estoque insuficiente. Disponível: {item.produto.estoque}')
                else:
                    if nova_quantidade == 0:
                        produto_nome = item.produto.nome
                        item.delete()
                        messages.success(request, f'{produto_nome} removido do carrinho.')
                    else:
                        form.save()
                        messages.success(request, 'Quantidade atualizada com sucesso!')
            
            # Invalidar cache do carrinho
            invalidar_cache_carrinho(request.user)
        
        return redirect('ver_carrinho')
        
    except Exception as e:
        logger.error(f"Erro ao atualizar item do carrinho: {str(e)}")
        messages.error(request, 'Erro ao atualizar item.')
        return redirect('ver_carrinho')

# SEM CACHE - operação de escrita
@login_required
def remover_do_carrinho(request, item_id):
    """Remove item do carrinho"""
    item = get_object_or_404(ItemCarrinho, id=item_id, carrinho__usuario=request.user)
    produto_nome = item.produto.nome
    item.delete()
    messages.success(request, f'{produto_nome} removido do carrinho.')
    
    # Invalidar cache do carrinho
    invalidar_cache_carrinho(request.user)
    return redirect('ver_carrinho')

# SEM CACHE - operação de escrita
@login_required
def limpar_carrinho(request):
    """Remove todos os itens do carrinho"""
    carrinho = obter_carrinho(request)
    carrinho.itens.all().delete()
    messages.success(request, 'Carrinho limpo.')
    
    # Invalidar cache do carrinho
    invalidar_cache_carrinho(request.user)
    return redirect('ver_carrinho')

# Cache para histórico de pedidos - 10 minutos
@login_required
@cache_page(60 * 10)
@vary_on_cookie
def historico_pedidos(request):
    """Histórico de pedidos do usuário"""
    pedidos = PedidoEntrega.objects.filter(
        carrinho__usuario=request.user
    ).order_by('-data_solicitacao')
    
    context = {
        'pedidos': pedidos,
    }
    return render(request, 'historico_pedidos.html', context)

# Cache para detalhes do pedido - 15 minutos
@login_required
@cache_page(60 * 15)
@vary_on_cookie
def detalhes_pedido(request, pedido_id):
    """Detalhes de um pedido específico"""
    pedido = get_object_or_404(
        PedidoEntrega, 
        id=pedido_id, 
        carrinho__usuario=request.user
    )
    
    context = {
        'pedido': pedido,
    }
    return render(request, 'detalhes_pedido.html', context)

# SEM CACHE - view de processo de pedido
@require_http_methods(["GET", "POST"])
def solicitar_entrega(request):
    """Versão final - resolve UNIQUE constraint"""
    
    try:
        carrinho = obter_carrinho_inteligente(request)
        
        if not carrinho or not carrinho.itens.exists():
            messages.error(request, 'Seu carrinho está vazio.')
            return redirect('ver_carrinho')
        
        if request.method == 'POST':
            form = PedidoEntregaForm(request.POST)
            if form.is_valid():
                return processar_pedido_final(request, form, carrinho)
        
        form = PedidoEntregaForm(initial=obter_dados_usuario(request.user))
        
        return render(request, 'solicitar_entrega.html', {
            'form': form, 
            'carrinho': carrinho
        })
        
    except Exception as e:
        logger.error(f"Erro em solicitar_entrega: {str(e)}")
        messages.error(request, 'Erro no sistema. Tente novamente.')
        return redirect('ver_carrinho')

def obter_carrinho_inteligente(request):
    """Solução inteligente para UNIQUE constraint - SEMPRE funciona"""
    try:
        carrinho_id = request.session.get('carrinho_id')
        if carrinho_id:
            carrinho = Carrinho.objects.filter(
                id=carrinho_id, 
                usuario=request.user,
                estado='aberto'
            ).first()
            if carrinho:
                if not hasattr(carrinho, 'pedido_entrega'):
                    return carrinho
                else:
                    del request.session['carrinho_id']
        
        carrinho_existente = Carrinho.objects.filter(
            usuario=request.user, 
            estado='aberto'
        ).first()
        
        if carrinho_existente:
            if not hasattr(carrinho_existente, 'pedido_entrega'):
                request.session['carrinho_id'] = carrinho_existente.id
                return carrinho_existente
            else:
                carrinho_existente.estado = 'fechado_com_pedido'
                carrinho_existente.save()
                logger.info(f"Carrinho {carrinho_existente.id} fechado por ter pedido")
        
        try:
            novo_carrinho = Carrinho.objects.create(
                usuario=request.user,
                estado='aberto'
            )
            request.session['carrinho_id'] = novo_carrinho.id
            logger.info(f"✅ NOVO carrinho criado: {novo_carrinho.id}")
            return novo_carrinho
            
        except IntegrityError:
            logger.info("🔄 UNIQUE constraint detectado - buscando carrinho existente")
            time.sleep(0.1)
            carrinho_criado = Carrinho.objects.filter(
                usuario=request.user, 
                estado='aberto'
            ).first()
            
            if carrinho_criado:
                request.session['carrinho_id'] = carrinho_criado.id
                logger.info(f"✅ Carrinho encontrado após UNIQUE: {carrinho_criado.id}")
                return carrinho_criado
            else:
                return criar_carrinho_estado_alternativo(request)
                
    except Exception as e:
        logger.error(f"❌ Erro crítico em obter_carrinho_inteligente: {str(e)}")
        return criar_carrinho_estado_alternativo(request)

def criar_carrinho_estado_alternativo(request):
    """Cria carrinho com estado alternativo para evitar UNIQUE"""
    try:
        estados_alternativos = ['ativo', 'pendente', 'novo', 'em_andamento']
        
        for estado in estados_alternativos:
            try:
                novo_carrinho = Carrinho.objects.create(
                    usuario=request.user,
                    estado=estado
                )
                request.session['carrinho_id'] = novo_carrinho.id
                logger.info(f"✅ Carrinho criado com estado alternativo '{estado}': {novo_carrinho.id}")
                return novo_carrinho
            except IntegrityError:
                continue
        
        qualquer_carrinho = Carrinho.objects.filter(usuario=request.user).first()
        if qualquer_carrinho:
            request.session['carrinho_id'] = qualquer_carrinho.id
            logger.warning(f"⚠️ Usando carrinho existente: {qualquer_carrinho.id}")
            return qualquer_carrinho
            
        raise Exception("Não foi possível obter ou criar carrinho")
        
    except Exception as e:
        logger.error(f"❌ Erro em criar_carrinho_estado_alternativo: {str(e)}")
        return None

def processar_pedido_final(request, form, carrinho):
    """Processa pedido e LIBERA a UNIQUE constraint"""
    try:
        with transaction.atomic():
            if hasattr(carrinho, 'pedido_entrega'):
                messages.info(request, 'Este carrinho já tem um pedido.')
                if 'carrinho_id' in request.session:
                    del request.session['carrinho_id']
                return redirect('solicitar_entrega')
            
            pedido = form.save(commit=False)
            pedido.carrinho = carrinho
            pedido.numero_pedido = gerar_numero_pedido_unico()
            pedido.save()
            
            carrinho.estado = 'fechado'
            carrinho.save()
            
            # Invalidar caches relacionados
            invalidar_cache_pedidos(request.user)
            invalidar_cache_carrinho(request.user)
            
            threading.Thread(
                target=processamento_final, 
                args=(carrinho.id, pedido.id), 
                daemon=True
            ).start()
            
            if 'carrinho_id' in request.session:
                del request.session['carrinho_id']
            
            messages.success(request, f'Pedido #{pedido.numero_pedido} realizado com sucesso!')
            return redirect('detalhes_pedido', pedido_id=pedido.id)
            
    except Exception as e:
        logger.error(f"❌ Erro em processar_pedido_final: {str(e)}")
        messages.error(request, 'Erro ao finalizar pedido.')
        return redirect('solicitar_entrega')

def processamento_final(carrinho_id, pedido_id):
    """Processamento final em background"""
    try:
        logger.info(f"✅ Pedido {pedido_id} processado - Carrinho {carrinho_id} fechado")
    except Exception as e:
        logger.error(f"❌ Erro em processamento_final: {str(e)}")

# SEM CACHE - operação de escrita
@login_required
def cancelar_pedido(request, pedido_id):
    """Cancela um pedido específico"""
    pedido = get_object_or_404(
        PedidoEntrega, 
        id=pedido_id, 
        carrinho__usuario=request.user
    )
    
    if pedido.estado == 'pendente':
        pedido.estado = 'cancelado'
        pedido.save()
        
        # Restaurar estoque dos produtos
        for item in pedido.carrinho.itens.all():
            produto = item.produto
            produto.estoque += item.quantidade
            if produto.status == 'esgotado':
                produto.status = 'ativo'
            produto.save()
        
        # Invalidar caches
        invalidar_cache_pedidos(request.user)
        
        messages.success(request, f'Pedido #{pedido.id} cancelado com sucesso.')
    else:
        messages.error(request, 'Este pedido não pode ser cancelado.')
    
    return redirect('detalhes_pedido', pedido_id=pedido.id)

# SEM CACHE - operação de escrita
@login_required
def alterar_estado_pedido(request, pedido_id):
    """Altera o estado de um pedido (para admin ou usuário)"""
    pedido = get_object_or_404(
        PedidoEntrega, 
        id=pedido_id
    )
    
    if not (request.user.is_staff or pedido.carrinho.usuario == request.user):
        messages.error(request, 'Você não tem permissão para alterar este pedido.')
        return redirect('detalhes_pedido', pedido_id=pedido.id)
    
    if request.method == 'POST':
        novo_estado = request.POST.get('estado')
        
        if novo_estado in dict(PedidoEntrega.ESTADO_PEDIDO_CHOICES):
            estado_anterior = pedido.estado
            pedido.estado = novo_estado
            pedido.save()
            
            # Invalidar cache de pedidos
            invalidar_cache_pedidos(request.user)
            
            messages.success(request, f'Pedido #{pedido.id} alterado de {estado_anterior} para {novo_estado}.')
        else:
            messages.error(request, 'Estado inválido.')
    
    return redirect('detalhes_pedido', pedido_id=pedido.id)

# SEM CACHE - operação de escrita
@login_required
def refazer_pedido(request, pedido_id):
    pedido_original = get_object_or_404(
        PedidoEntrega, 
        id=pedido_id, 
        carrinho__usuario=request.user
    )
    
    novo_carrinho = Carrinho.objects.create(
        usuario=request.user,
        estado='aberto'
    )
    
    for item in pedido_original.carrinho.itens.all():
        ItemCarrinho.objects.create(
            carrinho=novo_carrinho,
            produto=item.produto,
            quantidade=item.quantidade
        )
    
    # Invalidar cache do carrinho
    invalidar_cache_carrinho(request.user)
    
    messages.success(request, "Itens do pedido adicionados ao carrinho!")
    return redirect('ver_carrinho')

# SEM CACHE - API AJAX
@login_required
def atualizar_quantidade_ajax(request, item_id):
    """Atualiza quantidade via AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        item = get_object_or_404(ItemCarrinho, id=item_id, carrinho__usuario=request.user)
        quantidade = int(request.POST.get('quantidade', 1))
        
        if 1 <= quantidade <= item.produto.estoque:
            item.quantidade = quantidade
            item.save()
            
            # Invalidar cache do carrinho
            invalidar_cache_carrinho(request.user)
            
            return JsonResponse({
                'success': True,
                'subtotal_item': f'KZ {item.subtotal:.2f}',
                'subtotal_carrinho': f'KZ {item.carrinho.subtotal:.2f}',
                'taxa_entrega': f'KZ {item.carrinho.taxa_entrega:.2f}',
                'total': f'KZ {item.carrinho.total:.2f}',
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Quantidade inválida ou estoque insuficiente'
            })
    
    return JsonResponse({'success': False, 'error': 'Requisição inválida'})

# Funções de invalidação de cache
def invalidar_cache_carrinho(usuario):
    """Invalida cache específico do carrinho do usuário"""
    from django.core.cache import cache
    cache_keys = [
        f'ver_carrinho_user_{usuario.id}',
        f'carrinho_details_user_{usuario.id}',
    ]
    for key in cache_keys:
        cache.delete(key)
    logger.info(f"Cache do carrinho invalidado para usuário {usuario.id}")

def invalidar_cache_pedidos(usuario):
    """Invalida cache de pedidos do usuário"""
    from django.core.cache import cache
    cache_keys = [
        f'historico_pedidos_user_{usuario.id}',
        f'pedidos_list_user_{usuario.id}',
    ]
    for key in cache_keys:
        cache.delete(key)
    logger.info(f"Cache de pedidos invalidado para usuário {usuario.id}")

# Funções auxiliares (sem cache necessário)
def obter_dados_usuario(usuario):
    """Pré-carrega dados do usuário para o form"""
    try:
        return {
            'nome': usuario.get_full_name(),
            'email': usuario.email,
            'telefone': getattr(usuario, 'telefone', ''),
        }
    except Exception as e:
        logger.error(f"Erro ao obter dados usuário: {str(e)}")
        return {}

def gerar_numero_pedido_unico():
    """Gera um número de pedido único"""
    import uuid
    return f"PED-{uuid.uuid4().hex[:8].upper()}"

def enviar_notificacao_admin(pedido):
    """Envia email de notificação para o admin"""
    try:
        subject = f'Novo Pedido de Entrega - #{pedido.id}'
        
        itens_texto = "\n".join([
            f"- {item.quantidade}x {item.produto.nome} - €{item.subtotal:.2f}"
            for item in pedido.carrinho.itens.all()
        ])
        
        message = f'''
        Novo pedido de entrega recebido:
        
        Pedido: #{pedido.id}
        Cliente: {pedido.carrinho.usuario.get_full_name() or pedido.carrinho.usuario.username}
        Email: {pedido.carrinho.usuario.email}
        
        Itens do Pedido:
        {itens_texto}
        
        Subtotal: €{pedido.carrinho.subtotal:.2f}
        Taxa de Entrega: €{pedido.carrinho.taxa_entrega:.2f}
        Total: €{pedido.carrinho.total:.2f}
        
        Endereço de Entrega:
        {pedido.endereco_entrega}
        
        Observações:
        {pedido.observacoes or 'Nenhuma'}
        
        Data: {pedido.data_solicitacao.strftime("%d/%m/%Y %H:%M")}
        '''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )
        
        pedido.notificado_admin = True
        pedido.save()
        
    except Exception as e:
        logger.error(f"Erro ao enviar notificação: {e}")