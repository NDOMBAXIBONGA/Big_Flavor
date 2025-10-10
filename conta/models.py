from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

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
    
    # Datas personalizadas
    data_criacao = models.DateTimeField('Data de Criação', default=timezone.now)
    data_atualizacao = models.DateTimeField('Data de Atualização', auto_now=True)
    
    # CONFIGURAÇÕES
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome', 'cpf', 'username']
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        db_table = 'conta_usuario'
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        """Garante username único baseado no email"""
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