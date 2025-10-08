from django.db import models
from django.core.validators import MinLengthValidator
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