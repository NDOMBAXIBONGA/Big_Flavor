import os
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
import re
from django.core.validators import MinLengthValidator
from .models import Usuario
from datetime import date
from django.contrib.auth import get_user_model

User = get_user_model()

class ContactForm(forms.Form):
    full_name = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control", 
            "placeholder": "Seu nome completo"
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control", 
            "placeholder": "Digite seu email"
        })
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control", 
            "placeholder": "Digite sua mensagem"
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not "gmail.com" in email:
            raise ValidationError("O Email deve ser do gmail.com")
        return email

class RegistroUsuarioForm(forms.ModelForm):
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha',
            'minlength': '8'
        }),
        label='Senha',
        validators=[MinLengthValidator(8)]
    )
    
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua senha'
        }),
        label='Confirmar Senha'
    )
    
    class Meta:
        model = Usuario
        fields = ['nome', 'email', 'telemovel', 'cpf', 'data_nascimento', 
                 'bairro', 'cidade', 'provincia', 'municipio']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu@email.com'}),
            'telemovel': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu bairro'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sua cidade'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sua província'}),
            'municipio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu município'}),
        }

    PROVINCIAS = [
        ('', 'Selecione uma província'),
        ('huila', 'Huíla'),
        ('luanda', 'Luanda'),
        # ... outras províncias
    ]
    
    MUNICIPIOS_POR_PROVINCIA = {
        'huila': [
            ('', 'Selecione o município'),
            ('caconda', 'Caconda'),
            ('cacula', 'Cacula'),
            ('caluquembe', 'Caluquembe'),
            ('cuvango', 'Cuvango'),
            ('chibia', 'Chibia'),
            ('chicomba', 'Chicomba'),
            ('chipindo', 'Chipindo'),
            ('gambos', 'Gambos'),
            ('humpata', 'Humpata'),
            ('jamba', 'Jamba'),
            ('lubango', 'Lubango'),
            ('matala', 'Matala'),
            ('quilengues', 'Quilengues'),
            ('quipungo', 'Quipungo')
        ],
        'luanda': [
            ('', 'Selecione o município'),
            ('belas', 'Belas'),
            ('cacuaco', 'Cacuaco'),
            ('cazenga', 'Cazenga'),
            ('icolo_e_bengo', 'Icolo e Bengo'),
            ('luanda', 'Luanda'),
            ('quilamba_quiaxi', 'Quilamba Quiaxi'),
            ('kilamba_kiaxi', 'Kilamba Kiaxi'),
            ('talatona', 'Talatona'),
            ('viana', 'Viana')
        ],
        # ... outras províncias
    }
    
    provincia = forms.ChoiceField(
        choices=PROVINCIAS,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control', 
            'id': 'provincia-select',
            'onchange': 'carregarMunicipios()'
        }),
        label='Província'
    )
    
    municipio = forms.ChoiceField(
        choices=[('', 'Selecione primeiro a província')],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control', 
            'id': 'municipio-select',
            'disabled': 'disabled'
        }),
        label='Município'
    )
    
    def get_municipios_choices(self, provincia_id):
        """Retorna choices válidos para a província"""
        return self.MUNICIPIOS_POR_PROVINCIA.get(provincia_id, [('', 'Província inválida')])

    def clean_provincia(self):
        provincia = self.cleaned_data.get('provincia')
        provincias_validas = [code for code, name in self.PROVINCIAS if code]
        
        if provincia not in provincias_validas:
            raise ValidationError('Província inválida.')
        
        return provincia

    def clean_municipio(self):
        municipio = self.cleaned_data.get('municipio')
        provincia = self.cleaned_data.get('provincia')
        
        if provincia and municipio:
            municipios_validos = [code for code, name in self.get_municipios_choices(provincia) if code]
            if municipio not in municipios_validos:
                raise ValidationError('Município inválido para a província selecionada.')
        
        return municipio

    
    def clean_telemovel(self):
        telemovel = self.cleaned_data.get('telemovel')
        if telemovel:
            telemovel_limpo = re.sub(r'\D', '', telemovel)
            if len(telemovel_limpo) < 9:
                raise ValidationError('Número de telemóvel inválido')
            return telemovel_limpo
        return telemovel
    
    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            cpf_limpo = re.sub(r'\D', '', cpf)
            if len(cpf_limpo) != 11:
                raise ValidationError('CPF deve ter 11 dígitos')
            if Usuario.objects.filter(cpf=cpf_limpo).exists():
                raise ValidationError('Este CPF já está cadastrado')
            return cpf_limpo
        return cpf
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            if Usuario.objects.filter(email=email).exists():
                raise ValidationError('Este e-mail já está cadastrado')
            return email
        return email
    
    def clean_data_nascimento(self):
        data_nascimento = self.cleaned_data.get('data_nascimento')
        if not data_nascimento:
            raise ValidationError('Data de nascimento é obrigatória')
        
        hoje = date.today()
        if data_nascimento > hoje:
            raise ValidationError('Data de nascimento não pode ser no futuro')
        
        idade = hoje.year - data_nascimento.year
        if (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day):
            idade -= 1
        
        if idade < 18:
            raise ValidationError('Você deve ter pelo menos 18 anos para se registrar')
        
        return data_nascimento
    
    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        
        if senha and confirmar_senha and senha != confirmar_senha:
            raise ValidationError({'confirmar_senha': 'As senhas não coincidem'})
        
        return cleaned_data
    
    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data['senha'])
        if commit:
            usuario.save()
        return usuario

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'E-mail',
            'autocomplete': 'email'
        }),
        label='E-mail'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Senha'
        }),
        label='Senha'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'E-mail'

class EditarPerfilForm(forms.ModelForm):
    senha_atual = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sua senha atual'
        }),
        label='Senha Atual'
    )
    
    nova_senha = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nova senha'
        }),
        label='Nova Senha',
        min_length=6
    )
    
    confirmar_senha = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme a nova senha'
        }),
        label='Confirmar Nova Senha'
    )
    
    class Meta:
        model = Usuario
        fields = ['nome', 'email', 'telemovel', 'data_nascimento', 
                 'bairro', 'cidade', 'provincia', 'municipio']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu nome completo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu@email.com'}),
            'telemovel': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+244 900 000 000'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu bairro'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sua cidade'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sua província'}),
            'municipio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu município'}),
        }

    def clean_telemovel(self):
        telemovel = self.cleaned_data.get('telemovel')
        if telemovel:
            telemovel_limpo = re.sub(r'\D', '', telemovel)
            if len(telemovel_limpo) < 9:
                raise ValidationError('Número de telefone inválido. Deve ter pelo menos 9 dígitos.')
            return telemovel
        return telemovel

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
                raise ValidationError('Este e-mail já está em uso por outro utilizador.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        nova_senha = cleaned_data.get('nova_senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        senha_atual = cleaned_data.get('senha_atual')

        if nova_senha or confirmar_senha:
            if not senha_atual:
                self.add_error('senha_atual', 'Para alterar a senha, deve fornecer a senha atual.')
            elif nova_senha != confirmar_senha:
                self.add_error('confirmar_senha', 'As senhas não coincidem.')
            elif senha_atual and not self.instance.check_password(senha_atual):
                self.add_error('senha_atual', 'Senha atual incorreta.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        nova_senha = self.cleaned_data.get('nova_senha')
        if nova_senha:
            user.set_password(nova_senha)
        if commit:
            user.save()
        return user

class AvatarForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['foto_perfil']
        widgets = {
            'foto_perfil': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def clean_foto_perfil(self):
        foto_perfil = self.cleaned_data.get('foto_perfil')
        if not foto_perfil:
            return foto_perfil

        max_size = 5 * 1024 * 1024
        if foto_perfil.size > max_size:
            raise ValidationError('A imagem deve ter no máximo 5MB.')

        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(foto_perfil.name)[1].lower()
        if ext not in valid_extensions:
            raise ValidationError('Formato não suportado. Use JPG, PNG ou GIF.')

        return foto_perfil