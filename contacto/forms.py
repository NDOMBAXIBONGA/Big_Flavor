from django import forms
from django.core.exceptions import ValidationError
from .models import Contacto
import re

class ContactoForm(forms.ModelForm):
    # Campo adicional para confirmação de email (opcional)
    confirmar_email = forms.EmailField(
        label='Confirmar E-mail',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme seu e-mail'
        })
    )
    
    class Meta:
        model = Contacto
        fields = ['nome', 'email', 'telemovel', 'assunto', 'mensagem']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite seu nome completo',
                'autocomplete': 'name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'seu@email.com',
                'autocomplete': 'email'
            }),
            'telemovel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(+244) 900 000 000',
                'autocomplete': 'tel'
            }),
            'assunto': forms.Select(attrs={
                'class': 'form-control'
            }),
            'mensagem': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descreva sua mensagem em detalhes...',
                'rows': 6,
                'style': 'resize: vertical;'
            }),
        }
        labels = {
            'nome': 'Nome Completo',
            'email': 'E-mail',
            'telemovel': 'Telemóvel',
            'assunto': 'Assunto',
            'mensagem': 'Mensagem',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicionar classes CSS aos campos
        for field_name, field in self.fields.items():
            if field_name != 'assunto':  # O select já tem classe
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'
            
            # Adicionar required para campos obrigatórios
            if field.required:
                field.widget.attrs['required'] = 'required'
    
    def clean_telemovel(self):
        telemovel = self.cleaned_data.get('telemovel')
        if telemovel:
            # Remover caracteres não numéricos
            telemovel_limpo = re.sub(r'\D', '', telemovel)
            if len(telemovel_limpo) < 9:
                raise ValidationError('Número de telemóvel inválido. Deve ter pelo menos 9 dígitos.')
        return telemovel
    
    def clean_confirmar_email(self):
        email = self.cleaned_data.get('email')
        confirmar_email = self.cleaned_data.get('confirmar_email')
        
        if email and confirmar_email and email != confirmar_email:
            raise ValidationError('Os e-mails não coincidem.')
        
        return confirmar_email
    
    def clean(self):
        cleaned_data = super().clean()
        mensagem = cleaned_data.get('mensagem')
        
        # Validação adicional da mensagem
        if mensagem and len(mensagem.strip()) < 10:
            raise ValidationError({
                'mensagem': 'A mensagem deve ter pelo menos 10 caracteres.'
            })
        
        return cleaned_data