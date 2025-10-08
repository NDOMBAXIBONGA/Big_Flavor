from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.db import transaction
from .models import Carrinho, ItemCarrinho, PedidoEntrega
from .forms import AdicionarAoCarrinhoForm, PedidoEntregaForm, AtualizarItemForm
from menu.models import Produto

@login_required
def obter_carrinho(request):
    """Obtém ou cria carrinho para o usuário logado"""
    carrinho, created = Carrinho.objects.get_or_create(
        usuario=request.user,
        estado='aberto'
    )
    return carrinho

@login_required
def ver_carrinho(request):
    """Visualizar carrinho do usuário"""
    carrinho = obter_carrinho(request)
    itens = carrinho.itens.all()
    
    context = {
        'carrinho': carrinho,
        'itens': itens,
    }
    return render(request, 'ver_carrinho.html', context)

@login_required
def adicionar_ao_carrinho(request, produto_id):
    """Adiciona produto ao carrinho"""
    produto = get_object_or_404(Produto, id=produto_id, status='ativo')
    
    if not produto.em_estoque():
        messages.error(request, 'Produto indisponível no momento.')
        return redirect('lista_produtos')
    
    carrinho = obter_carrinho(request)
    
    if request.method == 'POST':
        form = AdicionarAoCarrinhoForm(request.POST)
        if form.is_valid():
            quantidade = form.cleaned_data['quantidade']
            
            # Verificar se há estoque suficiente
            if quantidade > produto.estoque:
                messages.error(request, f'Estoque insuficiente. Disponível: {produto.estoque}')
                return redirect('detalhes_produto', pk=produto_id)
            
            # Adicionar ou atualizar item no carrinho
            item, created = ItemCarrinho.objects.get_or_create(
                carrinho=carrinho,
                produto=produto,
                defaults={'quantidade': quantidade}
            )
            
            if not created:
                nova_quantidade = item.quantidade + quantidade
                if nova_quantidade > produto.estoque:
                    messages.error(request, f'Quantidade excede estoque disponível.')
                    return redirect('detalhes_produto', pk=produto_id)
                item.quantidade = nova_quantidade
                item.save()
                messages.success(request, f'Quantidade de {produto.nome} atualizada no carrinho.')
            else:
                messages.success(request, f'{produto.nome} adicionado ao carrinho!')
            
            return redirect('ver_carrinho')
    
    # Se for GET, redireciona para detalhes do produto
    return redirect('detalhes_produto', pk=produto_id)

@login_required
def atualizar_item_carrinho(request, item_id):
    """Atualiza quantidade de um item no carrinho"""
    item = get_object_or_404(ItemCarrinho, id=item_id, carrinho__usuario=request.user)
    
    if request.method == 'POST':
        form = AtualizarItemForm(request.POST, instance=item)
        if form.is_valid():
            nova_quantidade = form.cleaned_data['quantidade']
            
            # Verificar estoque
            if nova_quantidade > item.produto.estoque:
                messages.error(request, f'Estoque insuficiente. Disponível: {item.produto.estoque}')
            else:
                if nova_quantidade == 0:
                    item.delete()
                    messages.success(request, 'Item removido do carrinho.')
                else:
                    form.save()
                    messages.success(request, 'Quantidade atualizada.')
    
    return redirect('ver_carrinho')

@login_required
def remover_do_carrinho(request, item_id):
    """Remove item do carrinho"""
    item = get_object_or_404(ItemCarrinho, id=item_id, carrinho__usuario=request.user)
    produto_nome = item.produto.nome
    item.delete()
    messages.success(request, f'{produto_nome} removido do carrinho.')
    return redirect('ver_carrinho')

@login_required
def limpar_carrinho(request):
    """Remove todos os itens do carrinho"""
    carrinho = obter_carrinho(request)
    carrinho.itens.all().delete()
    messages.success(request, 'Carrinho limpo.')
    return redirect('ver_carrinho')

@login_required
def solicitar_entrega(request):
    """Solicita entrega do pedido"""
    carrinho = obter_carrinho(request)
    
    # Verificar se o carrinho tem itens
    if not carrinho.itens.exists():
        messages.error(request, 'Seu carrinho está vazio.')
        return redirect('ver_carrinho')
    
    # Verificar se todos os produtos estão disponíveis
    for item in carrinho.itens.all():
        if not item.produto.em_estoque() or item.quantidade > item.produto.estoque:
            messages.error(request, f'{item.produto.nome} não está mais disponível na quantidade solicitada.')
            return redirect('ver_carrinho')
    
    if request.method == 'POST':
        form = PedidoEntregaForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Criar pedido de entrega
                pedido = form.save(commit=False)
                pedido.carrinho = carrinho
                pedido.save()
                
                # Fechar carrinho
                carrinho.fechar_carrinho()
                
                # Notificar admin
                enviar_notificacao_admin(pedido)
                
                messages.success(request, 'Pedido de entrega solicitado com sucesso!')
                return redirect('detalhes_pedido', pedido_id=pedido.id)
    else:
        form = PedidoEntregaForm()
    
    context = {
        'form': form,
        'carrinho': carrinho,
    }
    return render(request, 'solicitar_entrega.html', context)

@login_required
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

@login_required
def historico_pedidos(request):
    """Histórico de pedidos do usuário"""
    pedidos = PedidoEntrega.objects.filter(
        carrinho__usuario=request.user
    ).order_by('-data_solicitacao')
    
    context = {
        'pedidos': pedidos,
    }
    return render(request, 'historico_pedidos.html', context)

# carrinho/views.py - na função enviar_notificacao_admin
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
        Cliente: {pedido.carrinho.usuario.nome}  # Use nome em vez de username
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
        
        # Marcar como notificado
        pedido.notificado_admin = True
        pedido.save()
        
    except Exception as e:
        print(f"Erro ao enviar notificação: {e}")
        
# API para atualizar quantidade via AJAX
@login_required
def atualizar_quantidade_ajax(request, item_id):
    """Atualiza quantidade via AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        item = get_object_or_404(ItemCarrinho, id=item_id, carrinho__usuario=request.user)
        quantidade = int(request.POST.get('quantidade', 1))
        
        if 1 <= quantidade <= item.produto.estoque:
            item.quantidade = quantidade
            item.save()
            
            return JsonResponse({
                'success': True,
                'subtotal_item': f'€{item.subtotal:.2f}',
                'subtotal_carrinho': f'€{item.carrinho.subtotal:.2f}',
                'taxa_entrega': f'€{item.carrinho.taxa_entrega:.2f}',
                'total': f'€{item.carrinho.total:.2f}',
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Quantidade inválida ou estoque insuficiente'
            })
    
    return JsonResponse({'success': False, 'error': 'Requisição inválida'})


@login_required
def cancelar_pedido(request, pedido_id):
    """Cancela um pedido específico"""
    pedido = get_object_or_404(
        PedidoEntrega, 
        id=pedido_id, 
        carrinho__usuario=request.user
    )
    
    # Só permite cancelar pedidos pendentes
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
        
        messages.success(request, f'Pedido #{pedido.id} cancelado com sucesso.')
    else:
        messages.error(request, 'Este pedido não pode ser cancelado.')
    
    return redirect('detalhes_pedido', pedido_id=pedido.id)

@login_required
def alterar_estado_pedido(request, pedido_id):
    """Altera o estado de um pedido (para admin ou usuário)"""
    pedido = get_object_or_404(
        PedidoEntrega, 
        id=pedido_id
    )
    
    # Verificar permissões
    if not (request.user.is_staff or pedido.carrinho.usuario == request.user):
        messages.error(request, 'Você não tem permissão para alterar este pedido.')
        return redirect('carrinho:detalhes_pedido', pedido_id=pedido.id)
    
    if request.method == 'POST':
        novo_estado = request.POST.get('estado')
        
        if novo_estado in dict(PedidoEntrega.ESTADO_PEDIDO_CHOICES):
            estado_anterior = pedido.estado
            pedido.estado = novo_estado
            pedido.save()
            
            # Log da alteração
            messages.success(request, f'Pedido #{pedido.id} alterado de {estado_anterior} para {novo_estado}.')
        else:
            messages.error(request, 'Estado inválido.')
    
    return redirect('detalhes_pedido', pedido_id=pedido.id)