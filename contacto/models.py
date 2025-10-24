from django.db import models
from django.core.validators import MinLengthValidator
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import re

class Contacto(models.Model):
    ASSUNTO_CHOICES = [
        ('', 'Selecione o assunto'),
        ('suporte', 'Suporte Técnico'),
        ('vendas', 'Informação de Vendas'),
        ('parceria', 'Proposta de Parceria'),
        ('reclamacao', 'Reclamação'),
        ('outro', 'Outro'),
    ]
    
    nome = models.CharField(
        max_length=100,
        verbose_name='Nome Completo',
        validators=[MinLengthValidator(2)]
    )
    
    email = models.EmailField(
        max_length=100,
        verbose_name='E-mail'
    )
    
    telemovel = models.CharField(
        max_length=15,
        verbose_name='Telemóvel'
    )
    
    assunto = models.CharField(
        max_length=20,
        choices=ASSUNTO_CHOICES,
        verbose_name='Assunto'
    )
    
    mensagem = models.TextField(
        max_length=1000,
        verbose_name='Mensagem',
        validators=[MinLengthValidator(10)]
    )
    
    data_envio = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Envio'
    )
    
    lido = models.BooleanField(
        default=False,
        verbose_name='Mensagem Lida'
    )
    
    respondido = models.BooleanField(
        default=False,
        verbose_name='Respondido'
    )
    
    class Meta:
        verbose_name = 'Contacto'
        verbose_name_plural = 'Contactos'
        ordering = ['-data_envio']
    
    def __str__(self):
        return f"{self.nome} - {self.assunto}"
    
    def clean(self):
        """Validações personalizadas"""
        from django.core.exceptions import ValidationError
        
        # Validar telemóvel (apenas números, mínimo 9 dígitos)
        if self.telemovel:
            telemovel_limpo = re.sub(r'\D', '', self.telemovel)
            if len(telemovel_limpo) < 9:
                raise ValidationError({
                    'telemovel': 'Número de telemóvel inválido. Deve ter pelo menos 9 dígitos.'
                })
    
    @classmethod
    def obter_contactos_nao_lidos(cls):
        """Obtém contactos não lidos com cache"""
        cache_key = 'contactos_nao_lidos'
        contactos = cache.get(cache_key)
        
        if contactos is None:
            contactos = list(cls.objects.filter(lido=False).order_by('-data_envio'))
            cache.set(cache_key, contactos, 300)  # Cache por 5 minutos
        
        return contactos
    
    @classmethod
    def obter_contactos_por_assunto(cls, assunto):
        """Obtém contactos por assunto com cache"""
        cache_key = f'contactos_assunto_{assunto}'
        contactos = cache.get(cache_key)
        
        if contactos is None:
            contactos = list(cls.objects.filter(assunto=assunto).order_by('-data_envio'))
            cache.set(cache_key, contactos, 600)  # Cache por 10 minutos
        
        return contactos
    
    @classmethod
    def obter_contactos_recentes(cls, limite=10):
        """Obtém contactos recentes com cache"""
        cache_key = f'contactos_recentes_{limite}'
        contactos = cache.get(cache_key)
        
        if contactos is None:
            contactos = list(cls.objects.all().order_by('-data_envio')[:limite])
            cache.set(cache_key, contactos, 300)  # Cache por 5 minutos
        
        return contactos
    
    @classmethod
    def obter_estatisticas_contactos(cls):
        """Obtém estatísticas de contactos com cache"""
        cache_key = 'estatisticas_contactos'
        estatisticas = cache.get(cache_key)
        
        if estatisticas is None:
            total_contactos = cls.objects.count()
            nao_lidos = cls.objects.filter(lido=False).count()
            respondidos = cls.objects.filter(respondido=True).count()
            
            # Contagem por assunto
            por_assunto = {}
            for assunto_val, assunto_label in cls.ASSUNTO_CHOICES[1:]:  # Pula o primeiro vazio
                if assunto_val:  # Garante que não é string vazia
                    count = cls.objects.filter(assunto=assunto_val).count()
                    por_assunto[assunto_val] = {
                        'label': assunto_label,
                        'count': count
                    }
            
            estatisticas = {
                'total_contactos': total_contactos,
                'nao_lidos': nao_lidos,
                'respondidos': respondidos,
                'por_assunto': por_assunto,
                'taxa_resposta': (respondidos / total_contactos * 100) if total_contactos > 0 else 0,
            }
            cache.set(cache_key, estatisticas, 900)  # Cache por 15 minutos
        
        return estatisticas
    
    @classmethod
    def obter_contactos_por_email(cls, email):
        """Obtém contactos por email com cache"""
        cache_key = f'contactos_email_{email.lower()}'
        contactos = cache.get(cache_key)
        
        if contactos is None:
            contactos = list(cls.objects.filter(email__iexact=email).order_by('-data_envio'))
            cache.set(cache_key, contactos, 1800)  # Cache por 30 minutos
        
        return contactos
    
    @classmethod
    def obter_contactos_por_periodo(cls, data_inicio, data_fim):
        """Obtém contactos por período com cache"""
        cache_key = f'contactos_periodo_{data_inicio}_{data_fim}'
        contactos = cache.get(cache_key)
        
        if contactos is None:
            contactos = list(cls.objects.filter(
                data_envio__date__gte=data_inicio,
                data_envio__date__lte=data_fim
            ).order_by('-data_envio'))
            cache.set(cache_key, contactos, 1800)  # Cache por 30 minutos
        
        return contactos
    
    @property
    def mensagem_resumida(self):
        """Retorna versão resumida da mensagem com cache"""
        cache_key = f'contacto_{self.id}_mensagem_resumida'
        mensagem_resumida = cache.get(cache_key)
        
        if mensagem_resumida is None:
            if len(self.mensagem) > 100:
                mensagem_resumida = self.mensagem[:100] + '...'
            else:
                mensagem_resumida = self.mensagem
            cache.set(cache_key, mensagem_resumida, 3600)  # Cache por 1 hora
        
        return mensagem_resumida
    
    @property
    def telemovel_formatado(self):
        """Retorna telemóvel formatado com cache"""
        cache_key = f'contacto_{self.id}_telemovel_formatado'
        telemovel_formatado = cache.get(cache_key)
        
        if telemovel_formatado is None:
            telemovel_limpo = re.sub(r'\D', '', self.telemovel)
            if len(telemovel_limpo) == 9:
                telemovel_formatado = f"{telemovel_limpo[:3]} {telemovel_limpo[3:6]} {telemovel_limpo[6:]}"
            else:
                telemovel_formatado = self.telemovel
            cache.set(cache_key, telemovel_formatado, 3600)  # Cache por 1 hora
        
        return telemovel_formatado
    
    def marcar_como_lido(self):
        """Marca o contacto como lido e limpa cache"""
        self.lido = True
        self.save()
        # Cache é limpo automaticamente pelo signal
    
    def marcar_como_respondido(self):
        """Marca o contacto como respondido e limpa cache"""
        self.respondido = True
        self.lido = True  # Se foi respondido, também foi lido
        self.save()
        # Cache é limpo automaticamente pelo signal
    
    def limpar_cache_contacto(self):
        """Limpa todo o cache relacionado a este contacto"""
        cache_keys = [
            f'contacto_{self.id}_mensagem_resumida',
            f'contacto_{self.id}_telemovel_formatado',
            'contactos_nao_lidos',
            'estatisticas_contactos',
            f'contactos_assunto_{self.assunto}',
            f'contactos_email_{self.email.lower()}',
            'contactos_recentes_10',
            'contactos_recentes_20',
            'contactos_recentes_50',
        ]
        cache.delete_many(cache_keys)
    
    def save(self, *args, **kwargs):
        """Sobrescreve save para limpar cache"""
        # Limpa cache antes de salvar se for uma atualização
        if self.pk:
            try:
                contacto_antigo = Contacto.objects.get(pk=self.pk)
                # Se assunto ou email mudaram, limpa caches específicos
                if contacto_antigo.assunto != self.assunto:
                    cache.delete(f'contactos_assunto_{contacto_antigo.assunto}')
                if contacto_antigo.email.lower() != self.email.lower():
                    cache.delete(f'contactos_email_{contacto_antigo.email.lower()}')
            except Contacto.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        self.limpar_cache_contacto()
    
    def delete(self, *args, **kwargs):
        """Limpa cache antes de deletar"""
        self.limpar_cache_contacto()
        super().delete(*args, **kwargs)

# Signal handlers para limpeza automática de cache
@receiver([post_save, post_delete], sender=Contacto)
def limpar_cache_contacto_signals(sender, instance, **kwargs):
    """Limpa caches globais quando contactos são modificados"""
    instance.limpar_cache_contacto()
    
    # Limpa caches adicionais
    cache.delete('total_contactos_hoje')
    cache.delete('contactos_ultima_semana')

# Funções utilitárias com cache
def obter_total_contactos_hoje():
    """Obtém total de contactos de hoje com cache"""
    from django.utils import timezone
    from datetime import datetime
    
    cache_key = 'total_contactos_hoje'
    total = cache.get(cache_key)
    
    if total is None:
        hoje = timezone.now().date()
        total = Contacto.objects.filter(data_envio__date=hoje).count()
        cache.set(cache_key, total, 300)  # Cache por 5 minutos
    
    return total

def obter_contactos_ultima_semana():
    """Obtém contactos da última semana com cache"""
    from django.utils import timezone
    from datetime import timedelta
    
    cache_key = 'contactos_ultima_semana'
    contactos_semana = cache.get(cache_key)
    
    if contactos_semana is None:
        uma_semana_atras = timezone.now() - timedelta(days=7)
        contactos_semana = list(Contacto.objects.filter(
            data_envio__gte=uma_semana_atras
        ).order_by('-data_envio'))
        cache.set(cache_key, contactos_semana, 1800)  # Cache por 30 minutos
    
    return contactos_semana

def obter_assuntos_mais_frequentes(limite=5):
    """Obtém assuntos mais frequentes com cache"""
    cache_key = f'assuntos_frequentes_{limite}'
    assuntos = cache.get(cache_key)
    
    if assuntos is None:
        from django.db.models import Count
        
        assuntos = list(Contacto.objects.exclude(assunto='').values(
            'assunto'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:limite])
        
        cache.set(cache_key, assuntos, 3600)  # Cache por 1 hora
    
    return assuntos

def buscar_contactos_por_termo(termo):
    """Busca contactos por termo com cache"""
    cache_key = f'busca_contactos_{termo.lower()}'
    resultados = cache.get(cache_key)
    
    if resultados is None:
        resultados = list(Contacto.objects.filter(
            models.Q(nome__icontains=termo) |
            models.Q(email__icontains=termo) |
            models.Q(mensagem__icontains=termo) |
            models.Q(telemovel__icontains=termo)
        ).order_by('-data_envio')[:50])  # Limita a 50 resultados
        
        cache.set(cache_key, resultados, 900)  # Cache por 15 minutos
    
    return resultados

# Função para limpar todo o cache de contactos (útil para admin)
def limpar_cache_contactos_global():
    """Limpa todo o cache relacionado a contactos"""
    cache.delete_many([
        'contactos_nao_lidos',
        'estatisticas_contactos',
        'total_contactos_hoje',
        'contactos_ultima_semana',
        'assuntos_frequentes_5',
        'assuntos_frequentes_10',
    ])
    
    # Para caches dinâmicos, precisaríamos de um padrão
    # Em produção, considere usar cache com prefixo específico