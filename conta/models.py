from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Usuario(AbstractUser):
    # Campos do AbstractUser que estamos mantendo
    username = models.CharField(
        'Nome de usuário', 
        max_length=150, 
        unique=True,
        blank=True, 
        null=True
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
        null=True,
        default=None
    )
    
    # Controle de usuário
    data_criacao = models.DateTimeField('Data de Criação', default=timezone.now)
    data_atualizacao = models.DateTimeField('Data de Atualização', auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome', 'cpf', 'username']
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f'{self.nome} ({self.email})'
    
    def get_full_name(self):
        return self.nome
    
    def get_short_name(self):
        return self.nome.split(' ')[0] if self.nome else ''
    
    def save(self, *args, **kwargs):
        if not self.username and self.email:
            self.username = self.email.split('@')[0]
        super().save(*args, **kwargs)