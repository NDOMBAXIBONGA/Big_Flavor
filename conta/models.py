from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class Usuario(AbstractUser):
    # TORNAR username OPCIONAL no banco, mas manter no modelo
    username = models.CharField(
        'Nome de usuário',
        max_length=150,
        unique=True,
        blank=True,
        null=True,  # Permite NULL no banco
        default=None  # Valor padrão
    )
    
    # Campos personalizados
    email = models.EmailField('E-mail', unique=True, max_length=100)
    nome = models.CharField('Nome Completo', max_length=100)
    telemovel = models.CharField('Telemóvel', max_length=15, blank=True, null=True)
    cpf = models.CharField('CPF', max_length=14, unique=True)
    data_nascimento = models.DateField('Data de Nascimento', blank=True, null=True)
    
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
    
    # Datas
    data_criacao = models.DateTimeField('Data de Criação', default=timezone.now)
    data_atualizacao = models.DateTimeField('Data de Atualização', auto_now=True)
    
    # CONFIGURAÇÕES CORRIGIDAS
    USERNAME_FIELD = 'email'  # Login com email
    REQUIRED_FIELDS = ['nome', 'cpf']  # REMOVA username daqui
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-data_criacao']
        db_table = 'conta_usuario'
    
    def __str__(self):
        return f'{self.nome} ({self.email})'
    
    def get_full_name(self):
        return self.nome
    
    def get_short_name(self):
        return self.nome.split(' ')[0] if self.nome else ''
    
    def save(self, *args, **kwargs):
        """GARANTE que sempre tenha um username antes de salvar"""
        if not self.username:
            # Gera username único baseado no email
            base_username = self.email.split('@')[0]
            username = base_username
            counter = 1
            
            # Verifica se username já existe
            while Usuario.objects.filter(username=username).exclude(pk=self.pk).exists():
                username = f"{base_username}{counter}"
                counter += 1
                if counter > 100:  # Prevenção de loop infinito
                    username = f"{base_username}_{uuid.uuid4().hex[:8]}"
                    break
            
            self.username = username
        
        # Garante que o email esteja em lowercase
        if self.email:
            self.email = self.email.lower()
            
        super().save(*args, **kwargs)