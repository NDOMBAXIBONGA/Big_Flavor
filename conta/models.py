from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
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

class Usuario(AbstractBaseUser, PermissionsMixin):
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
    
    # Campos de controle do usuário (OBRIGATÓRIOS)
    is_staff = models.BooleanField('Membro da equipe', default=False)
    is_active = models.BooleanField('Ativo', default=True)
    
    # Datas
    data_criacao = models.DateTimeField('Data de Criação', default=timezone.now)
    data_atualizacao = models.DateTimeField('Data de Atualização', auto_now=True)
    last_login = models.DateTimeField('Último login', blank=True, null=True)
    date_joined = models.DateTimeField('Data de registro', default=timezone.now)
    
    # ADICIONE ESTES CAMPOS QUE ESTAVAM FALTANDO
    first_name = models.CharField('Primeiro nome', max_length=150, blank=True)
    last_name = models.CharField('Sobrenome', max_length=150, blank=True)
    
    objects = UsuarioManager()
    
    # CONFIGURAÇÕES CORRETAS
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome', 'cpf']
    
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
        """Garante que o email esteja em lowercase"""
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)