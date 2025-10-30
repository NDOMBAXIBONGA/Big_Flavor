from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class Usuario(AbstractUser):
    # Remove o username padrão se quiser usar apenas email
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True
    )
    
    # Campos personalizados
    email = models.EmailField('E-mail', unique=True)
    nome = models.CharField('Nome Completo', max_length=100)
    telemovel = models.CharField('Telemóvel', max_length=15, blank=True, null=True)
    
    # Endereço
    bairro = models.CharField('Bairro', max_length=100, blank=True, null=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True, null=True)
    provincia = models.CharField('Província', max_length=50, blank=True, null=True)
    municipio = models.CharField('Município', max_length=50, blank=True, null=True)

    foto_perfil = models.ImageField(
        'Foto de Perfil',
        upload_to='avatars/%Y/%m/%d/',
        blank=True,
        null=True
    )
    
    # Datas personalizadas
    data_criacao = models.DateTimeField('Data de Criação', default=timezone.now)
    data_atualizacao = models.DateTimeField('Data de Atualização', auto_now=True)
    
    # CONFIGURAÇÕES
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome', 'username']
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        db_table = 'conta_usuario'
    
    def __str__(self):
        return self.email
    
    @classmethod
    def obter_por_email(cls, email):
        """Obtém usuário por email com cache"""
        cache_key = f'usuario_email_{email.lower()}'
        usuario = cache.get(cache_key)
        
        if usuario is None:
            try:
                usuario = cls.objects.get(email=email.lower())
                cache.set(cache_key, usuario, 3600)  # Cache por 1 hora
            except cls.DoesNotExist:
                cache.set(cache_key, None, 300)  # Cache negativo por 5 minutos
                return None
        return usuario
    
    @classmethod
    def obter_por_id(cls, user_id):
        """Obtém usuário por ID com cache"""
        cache_key = f'usuario_id_{user_id}'
        usuario = cache.get(cache_key)
        
        if usuario is None:
            try:
                usuario = cls.objects.get(id=user_id)
                cache.set(cache_key, usuario, 3600)  # Cache por 1 hora
            except cls.DoesNotExist:
                cache.set(cache_key, None, 300)  # Cache negativo por 5 minutos
                return None
        return usuario
    
    @classmethod
    def obter_todos_usuarios(cls):
        """Obtém todos os usuários com cache"""
        cache_key = 'todos_usuarios'
        usuarios = cache.get(cache_key)
        
        if usuarios is None:
            usuarios = list(cls.objects.all().order_by('-data_criacao'))
            cache.set(cache_key, usuarios, 1800)  # Cache por 30 minutos
        
        return usuarios
    
    @classmethod
    def obter_usuarios_ativos(cls):
        """Obtém usuários ativos com cache"""
        cache_key = 'usuarios_ativos'
        usuarios = cache.get(cache_key)
        
        if usuarios is None:
            usuarios = list(cls.objects.filter(is_active=True).order_by('-date_joined'))
            cache.set(cache_key, usuarios, 1800)  # Cache por 30 minutos
        
        return usuarios
    
    @property
    def nome_completo(self):
        """Cache para nome completo"""
        cache_key = f'usuario_{self.id}_nome_completo'
        nome = cache.get(cache_key)
        
        if nome is None:
            nome = f"{self.first_name} {self.last_name}".strip() or self.nome
            cache.set(cache_key, nome, 3600)  # Cache por 1 hora
        
        return nome
    
    @property
    def informacoes_perfil(self):
        """Cache para informações completas do perfil"""
        cache_key = f'usuario_{self.id}_informacoes_perfil'
        informacoes = cache.get(cache_key)
        
        if informacoes is None:
            informacoes = {
                'nome': self.nome_completo,
                'email': self.email,
                'telemovel': self.telemovel,
                'cidade': self.cidade,
                'provincia': self.provincia,
                'data_criacao': self.data_criacao,
                'is_staff': self.is_staff,
                'is_active': self.is_active,
            }
            cache.set(cache_key, informacoes, 1800)  # Cache por 30 minutos
        
        return informacoes
    
    def get_estatisticas_usuario(self):
        """Obtém estatísticas do usuário com cache"""
        cache_key = f'usuario_{self.id}_estatisticas'
        estatisticas = cache.get(cache_key)
        
        if estatisticas is None:
            from carinho.models import PedidoEntrega, Carrinho
            
            total_pedidos = PedidoEntrega.objects.filter(
                carrinho__usuario=self
            ).count()
            
            pedidos_ativos = PedidoEntrega.objects.filter(
                carrinho__usuario=self,
                estado__in=['pendente', 'confirmado', 'preparacao']
            ).count()
            
            carrinho_aberto = Carrinho.objects.filter(
                usuario=self,
                estado='aberto'
            ).exists()
            
            estatisticas = {
                'total_pedidos': total_pedidos,
                'pedidos_ativos': pedidos_ativos,
                'carrinho_aberto': carrinho_aberto,
                'ultimo_login': self.last_login,
                'membro_desde': self.data_criacao,
            }
            cache.set(cache_key, estatisticas, 900)  # Cache por 15 minutos
        
        return estatisticas
    
    def limpar_cache_usuario(self):
        """Limpa todo o cache relacionado a este usuário"""
        cache_keys = [
            f'usuario_id_{self.id}',
            f'usuario_email_{self.email.lower()}',
            f'usuario_{self.id}_nome_completo',
            f'usuario_{self.id}_informacoes_perfil',
            f'usuario_{self.id}_estatisticas',
            f'carrinho_aberto_usuario_{self.id}',
            f'pedidos_usuario_{self.id}',
            f'carrinho_com_itens_usuario_{self.id}',
        ]
        cache.delete_many(cache_keys)
        
        # Também limpa caches globais que podem conter este usuário
        cache.delete('todos_usuarios')
        cache.delete('usuarios_ativos')
        cache.delete('estatisticas_usuarios')
    
    def save(self, *args, **kwargs):
        """Garante username único baseado no email e limpa cache"""
        # Limpa cache antes de salvar se for uma atualização
        if self.pk:
            try:
                usuario_antigo = Usuario.objects.get(pk=self.pk)
                # Se email mudou, limpa caches específicos
                if usuario_antigo.email != self.email:
                    cache.delete(f'usuario_email_{usuario_antigo.email.lower()}')
            except Usuario.DoesNotExist:
                pass
        
        if not self.username and self.email:
            self.username = self.email.split('@')[0]
            
        # Verifica se username já existe
        if self.username:
            counter = 1
            original_username = self.username
            while Usuario.objects.filter(username=self.username).exclude(pk=self.pk).exists():
                self.username = f"{original_username}{counter}"
                counter += 1
                if counter > 100:
                    import uuid
                    self.username = f"{original_username}_{uuid.uuid4().hex[:8]}"
                    break
        
        if self.email:
            self.email = self.email.lower()
            
        super().save(*args, **kwargs)
        
        # Limpa cache após salvar
        self.limpar_cache_usuario()

    def delete(self, *args, **kwargs):
        """Limpa cache antes de deletar"""
        self.limpar_cache_usuario()
        super().delete(*args, **kwargs)

# Signal handlers para limpeza automática de cache
@receiver([post_save, post_delete], sender=Usuario)
def limpar_cache_usuario_signals(sender, instance, **kwargs):
    """Limpa caches globais quando usuários são modificados"""
    cache.delete('todos_usuarios')
    cache.delete('usuarios_ativos')
    cache.delete('estatisticas_usuarios')
    
    # Limpa cache de estatísticas se for criação/exclusão
    if kwargs.get('created') or kwargs.get('signal') == post_delete:
        cache.delete('total_usuarios')
        cache.delete('novos_usuarios_ultima_semana')

# Funções utilitárias com cache
def obter_estatisticas_usuarios():
    """Obtém estatísticas gerais de usuários com cache"""
    cache_key = 'estatisticas_usuarios'
    estatisticas = cache.get(cache_key)
    
    if estatisticas is None:
        from django.utils import timezone
        from datetime import timedelta
        
        uma_semana_atras = timezone.now() - timedelta(days=7)
        
        total_usuarios = Usuario.objects.count()
        usuarios_ativos = Usuario.objects.filter(is_active=True).count()
        novos_esta_semana = Usuario.objects.filter(
            data_criacao__gte=uma_semana_atras
        ).count()
        staff_users = Usuario.objects.filter(is_staff=True).count()
        
        estatisticas = {
            'total_usuarios': total_usuarios,
            'usuarios_ativos': usuarios_ativos,
            'novos_esta_semana': novos_esta_semana,
            'staff_users': staff_users,
            'ultima_atualizacao': timezone.now()
        }
        cache.set(cache_key, estatisticas, 1800)  # Cache por 30 minutos
    
    return estatisticas

def obter_usuario_por_identificador(identificador):
    """
    Busca usuário por email ou ID com cache
    """
    # Tenta por email
    usuario = Usuario.obter_por_email(identificador)
    if usuario:
        return usuario
    
    # Tenta por ID (se for numérico)
    if identificador.isdigit():
        usuario = Usuario.obter_por_id(int(identificador))
        if usuario:
            return usuario
    
    return None

def buscar_usuarios_por_nome(nome):
    """Busca usuários por nome com cache"""
    cache_key = f'busca_usuarios_nome_{nome.lower()}'
    usuarios = cache.get(cache_key)
    
    if usuarios is None:
        usuarios = list(Usuario.objects.filter(
            models.Q(nome__icontains=nome) |
            models.Q(first_name__icontains=nome) |
            models.Q(last_name__icontains=nome) |
            models.Q(email__icontains=nome)
        ).order_by('nome')[:50])  # Limita a 50 resultados
        cache.set(cache_key, usuarios, 900)  # Cache por 15 minutos
    
    return usuarios

# Método para limpar cache específico de usuários (útil para admin)
def limpar_cache_usuarios_global():
    """Limpa todo o cache relacionado a usuários"""
    from django.core.cache import cache
    # Não podemos listar todas as chaves, então focamos nas conhecidas
    cache.delete_many([
        'todos_usuarios',
        'usuarios_ativos',
        'estatisticas_usuarios',
        'total_usuarios',
        'novos_usuarios_ultima_semana'
    ])
    
    # Para caches específicos de usuários, precisaríamos de um padrão
    # Em produção, considere usar cache com prefixo específico