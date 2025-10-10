from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    def create_user(self, email, nome, cpf, password=None, **extra_fields):
        if not email:
            raise ValueError('O usuário deve ter um endereço de email')
        if not nome:
            raise ValueError('O usuário deve ter um nome completo')
        if not cpf:
            raise ValueError('O usuário deve ter um CPF')
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nome=nome,
            cpf=cpf,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, cpf, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuário deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuário deve ter is_superuser=True.')

        return self.create_user(email, nome, cpf, password, **extra_fields)


class Usuario(AbstractUser):
    # Dados básicos
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
    is_active = models.BooleanField('Ativo', default=True)
    is_staff = models.BooleanField('Equipe', default=False)
    is_superuser = models.BooleanField('Superusuário', default=False)
    
    objects = UsuarioManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome', 'cpf']
    
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


# REMOVA o modelo PerfilUsuario - você não precisa dele pois já tem Usuario personalizado
# REMOVA também os signals relacionados ao User padrão do Django

# REMOVA o formulário EditarPerfilForm do models.py - ele deve estar em forms.py separado