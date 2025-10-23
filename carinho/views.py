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
from django.views.decorators.http import require_http_methods
import logging
import threading

logger = logging.getLogger(__name__)


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
    carrinho = Carrinho.obter_carrinho_aberto(request.user)
    itens = carrinho.itens.all()
    
    context = {
        'carrinho': carrinho,
        'itens': itens,
    }
    return render(request, 'ver_carrinho.html', context)

@login_required
def adicionar_ao_carrinho(request, produto_id):
    """Adiciona produto ao carrinho - VERSÃO CORRIGIDA"""
    try:
        # Use apenas UMA abordagem
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
                
                return redirect('ver_carrinho')
        
        return redirect('detalhes_produto', pk=produto_id)
        
    except Exception as e:
        messages.error(request, f'Erro ao adicionar produto: {str(e)}')
        return redirect('lista_produtos')

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

from django.db import transaction, IntegrityError
from django.shortcuts import redirect, render
from django.contrib import messages
from django.views.decorators.http import require_http_methods
import threading
import logging
import time

logger = logging.getLogger(__name__)

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
        # ✅ 1. PRIMEIRO: Tenta usar carrinho da sessão
        carrinho_id = request.session.get('carrinho_id')
        if carrinho_id:
            carrinho = Carrinho.objects.filter(
                id=carrinho_id, 
                usuario=request.user,
                estado='aberto'
            ).first()
            if carrinho:
                # Verifica se não tem pedido associado
                if not hasattr(carrinho, 'pedido_entrega'):
                    return carrinho
                else:
                    # Se tem pedido, remove da sessão e continua
                    del request.session['carrinho_id']
        
        # ✅ 2. SEGUNDO: Busca carrinho aberto existente (pode ser apenas UM por usuário)
        carrinho_existente = Carrinho.objects.filter(
            usuario=request.user, 
            estado='aberto'
        ).first()
        
        if carrinho_existente:
            # ✅ VERIFICA se este carrinho já tem pedido
            if not hasattr(carrinho_existente, 'pedido_entrega'):
                request.session['carrinho_id'] = carrinho_existente.id
                return carrinho_existente
            else:
                # ✅ SE TEM PEDIDO: muda estado para não interferir com UNIQUE
                carrinho_existente.estado = 'fechado_com_pedido'
                carrinho_existente.save()
                logger.info(f"Carrinho {carrinho_existente.id} fechado por ter pedido")
        
        # ✅ 3. TERCEIRO: Tenta criar novo carrinho com tratamento de erro
        try:
            novo_carrinho = Carrinho.objects.create(
                usuario=request.user,
                estado='aberto'
            )
            request.session['carrinho_id'] = novo_carrinho.id
            logger.info(f"✅ NOVO carrinho criado: {novo_carrinho.id}")
            return novo_carrinho
            
        except IntegrityError:
            # ❌ UNIQUE constraint - outro processo criou o carrinho
            logger.info("🔄 UNIQUE constraint detectado - buscando carrinho existente")
            
            # ✅ Busca o carrinho que foi criado
            time.sleep(0.1)  # Pequena pausa para garantir commit
            carrinho_criado = Carrinho.objects.filter(
                usuario=request.user, 
                estado='aberto'
            ).first()
            
            if carrinho_criado:
                request.session['carrinho_id'] = carrinho_criado.id
                logger.info(f"✅ Carrinho encontrado após UNIQUE: {carrinho_criado.id}")
                return carrinho_criado
            else:
                # ✅ ÚLTIMO RECURSO: usa estado diferente
                return criar_carrinho_estado_alternativo(request)
                
    except Exception as e:
        logger.error(f"❌ Erro crítico em obter_carrinho_inteligente: {str(e)}")
        return criar_carrinho_estado_alternativo(request)

def criar_carrinho_estado_alternativo(request):
    """Cria carrinho com estado alternativo para evitar UNIQUE"""
    try:
        # Tenta estados alternativos
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
                continue  # Tenta próximo estado
        
        # Se todos os estados falharem, busca qualquer carrinho
        qualquer_carrinho = Carrinho.objects.filter(usuario=request.user).first()
        if qualquer_carrinho:
            request.session['carrinho_id'] = qualquer_carrinho.id
            logger.warning(f"⚠️ Usando carrinho existente: {qualquer_carrinho.id}")
            return qualquer_carrinho
            
        # Último recurso absoluto
        raise Exception("Não foi possível obter ou criar carrinho")
        
    except Exception as e:
        logger.error(f"❌ Erro em criar_carrinho_estado_alternativo: {str(e)}")
        return None

def processar_pedido_final(request, form, carrinho):
    """Processa pedido e LIBERA a UNIQUE constraint"""
    try:
        with transaction.atomic():
            # Verificação final de segurança
            if hasattr(carrinho, 'pedido_entrega'):
                messages.info(request, 'Este carrinho já tem um pedido.')
                if 'carrinho_id' in request.session:
                    del request.session['carrinho_id']
                return redirect('solicitar_entrega')
            
            pedido = form.save(commit=False)
            pedido.carrinho = carrinho
            pedido.numero_pedido = gerar_numero_pedido_unico()
            pedido.save()
            
            # ✅ CRÍTICO: Muda o estado para LIBERAR a UNIQUE constraint
            carrinho.estado = 'fechado'
            carrinho.save()
            
            # Processamento em background
            threading.Thread(
                target=processamento_final, 
                args=(carrinho.id, pedido.id), 
                daemon=True
            ).start()
            
            # Limpa sessão para próximo pedido
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
        # Aqui você pode adicionar:
        # - Limpeza de itens do carrinho
        # - Notificações
        # - Etc.
        
        logger.info(f"✅ Pedido {pedido_id} processado - Carrinho {carrinho_id} fechado")
        
    except Exception as e:
        logger.error(f"❌ Erro em processamento_final: {str(e)}")

def limpar_carrinhos_duplicados(usuario):
    """Limpa carrinhos duplicados (para admin)"""
    try:
        from django.db.models import Count
        
        # Encontra usuários com múltiplos carrinhos abertos
        usuarios_com_duplicados = Carrinho.objects.filter(
            estado='aberto'
        ).values('usuario').annotate(
            total=Count('id')
        ).filter(total__gt=1)
        
        for usuario_data in usuarios_com_duplicados:
            user_id = usuario_data['usuario']
            carrinhos = Carrinho.objects.filter(
                usuario_id=user_id, 
                estado='aberto'
            ).order_by('-data_criacao')
            
            # Mantém o mais recente, fecha os outros
            if carrinhos.count() > 1:
                carrinho_manter = carrinhos.first()
                carrinhos.exclude(id=carrinho_manter.id).update(estado='fechado_duplicado')
                logger.info(f"Limpos {carrinhos.count() - 1} carrinhos duplicados do usuário {user_id}")
                
        return usuarios_com_duplicados.count()
        
    except Exception as e:
        logger.error(f"Erro ao limpar carrinhos duplicados: {str(e)}")
        return 0

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

def listar_pedidos_ativos_usuario(usuario):
    """Lista pedidos ativos do usuário (para debug)"""
    return PedidoEntrega.objects.filter(
        carrinho__usuario=usuario,
        carrinho__estado='aberto'
    )

def limpar_carrinhos_abandonados(usuario):
    """Limpa carrinhos abertos sem itens (manutenção)"""
    carrinhos_abandonados = Carrinho.objects.filter(
        usuario=usuario,
        estado='aberto',
        itens__isnull=True
    ).delete()
    return carrinhos_abandonados

def gerar_numero_pedido_unico():
    """Gera um número de pedido único"""
    import uuid
    from django.utils import timezone
    
    # Opção 1: UUID (mais seguro)
    return f"PED-{uuid.uuid4().hex[:8].upper()}"
    
    # Opção 2: Timestamp + random
    # return f"PED-{int(timezone.now().timestamp())}-{random.randint(1000, 9999)}"

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

@login_required
def refazer_pedido(request, pedido_id):
    pedido_original = get_object_or_404(
        PedidoEntrega, 
        id=pedido_id, 
        carrinho__usuario=request.user
    )
    
    # Cria um novo carrinho baseado no pedido original
    novo_carrinho = Carrinho.objects.create(
        usuario=request.user,
        estado='aberto'
    )
    
    # Copia os itens do pedido original para o novo carrinho
    for item in pedido_original.carrinho.itens.all():
        ItemCarrinho.objects.create(
            carrinho=novo_carrinho,
            produto=item.produto,
            quantidade=item.quantidade
        )
    
    messages.success(request, "Itens do pedido adicionados ao carrinho!")
    return redirect('ver_carrinho')