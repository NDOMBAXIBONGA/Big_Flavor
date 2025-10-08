import os
from django.contrib.auth.models import User
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
        widget=forms.TextInput(
            attrs={
                    "class": "form-control", 
                    "placeholder": "Seu nome completo"
                }
            )
        )
    email     = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                    "class": "form-control", 
                    "placeholder": "Digite seu email"
                }
            )
        )
    content   = forms.CharField(
        widget=forms.Textarea(
            attrs={
                    "class": "form-control", 
                    "placeholder": "Digite sua mensagem"
                }
            )
        )
    
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not "gmail.com" in email:
            raise forms.ValidationError("O Email deve ser do gmail.com")
        return email

#class LoginForm(forms.Form):
#    username = forms.CharField()
#    password = forms.CharField(widget=forms.PasswordInput)

#class RegisterForm(forms.Form):
#    username = forms.CharField()
#    email = forms.EmailField()
#    password = forms.CharField(widget=forms.PasswordInput)
#    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

#   def clean_username(self):
#        username = self.cleaned_data.get('username')
#        qs = User.objects.filter(username=username)
#        if qs.exists():
#            raise forms.ValidationError("Esse usuário já existe, escolha outro nome.")
#        return username
    
#    def clean_email(self):
#        email = self.cleaned_data.get('email')
#        qs = User.objects.filter(email=email)

#        if qs.exists():
#            raise forms.ValidationError("Esse email já existe, tente outro!")
#        return email

#    def clean(self):
#        data = self.cleaned_data
#        password = self.cleaned_data.get('password')
#        password2 = self.cleaned_data.get('password2')
#        if password != password2:
#            raise forms.ValidationError("As senhas informadas devem ser iguais!")
#        return data

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
            'provincia': forms.Select(attrs={'class': 'form-control', 'id': 'provincia-select'}),
            'municipio': forms.Select(attrs={'class': 'form-control', 'id': 'municipio-select'}),
        }
    
    PROVINCIAS = [
        ('', 'Selecione uma província'),
        ('luanda', 'Luanda'),
        ('benguela', 'Benguela'),
        ('huila', 'Huíla'),
        # ... outras províncias
    ]
    
    provincia = forms.ChoiceField(
        choices=PROVINCIAS,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'provincia-select'}),
        label='Província'
    )
    
    municipio = forms.ChoiceField(
        choices=[],  # Inicialmente vazio
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'municipio-select'}),
        label='Município'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Se já tem dados POST, atualiza os municípios
        if 'provincia' in self.data:
            provincia = self.data.get('provincia')
            self.fields['municipio'].choices = self.get_municipios_choices(provincia)
        else:
            self.fields['municipio'].choices = [('', 'Selecione a província primeiro')]

    def get_municipios_choices(self, provincia_id):
        """Retorna choices válidos para a província"""
        MUNICIPIOS_POR_PROVINCIA = {
            'luanda': [
                ('', 'Selecione o município'),
                ('belas', 'Belas'),
                ('cacuaco', 'Cacuaco'),
                ('cazenga', 'Cazenga'),
                ('icolo-e-bengo', 'Icolo e Bengo'),
                ('luanda', 'Luanda'),
                ('quilamba-quiaxi', 'Quilamba Quiaxi'),
                ('talatona', 'Talatona'),
                ('viana', 'Viana')
            ],
            'benguela': [
                ('', 'Selecione o município'),
                ('benguela', 'Benguela'),
                ('baia-farta', 'Baía Farta'),
                ('balombo', 'Balombo'),
                ('bocoio', 'Bocoio'),
                ('caimbambo', 'Caimbambo'),
                ('catumbela', 'Catumbela'),
                ('chongoroi', 'Chongoroi'),
                ('cubal', 'Cubal'),
                ('ganda', 'Ganda'),
                ('lobito', 'Lobito')
            ],
            # ... outras províncias
        }
        return MUNICIPIOS_POR_PROVINCIA.get(provincia_id, [('', 'Província inválida')])

    def clean_provincia(self):
        provincia = self.cleaned_data.get('provincia')
        provincias_validas = [code for code, name in self.PROVINCIAS if code]
        
        if provincia not in provincias_validas:
            raise ValidationError('Província inválida.')
        
        return provincia

    def clean_municipio(self):
        municipio = self.cleaned_data.get('municipio')
        provincia = self.cleaned_data.get('provincia')
        
        if provincia:
            municipios_validos = [code for code, name in self.get_municipios_choices(provincia) if code]
            if municipio not in municipios_validos:
                raise ValidationError('Município inválido para a província selecionada.')
        
        return municipio
    
    def clean_telemovel(self):
        telemovel = self.cleaned_data['telemovel']
        telemovel_limpo = re.sub(r'\D', '', telemovel)
        
        if len(telemovel_limpo) < 9:
            raise ValidationError('Número de telemóvel inválido')
        
        return telemovel_limpo
    
    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        cpf_limpo = re.sub(r'\D', '', cpf)
        
        if len(cpf_limpo) != 14:
            raise ValidationError('CPF deve ter 14 dígitos')
        
        if Usuario.objects.filter(cpf=cpf_limpo).exists():
            raise ValidationError('Este CPF já está cadastrado')
        
        return cpf_limpo
    
    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este e-mail já está cadastrado')
        
        return email
    
    
    def clean_data_nascimento(self):
        data_nascimento = self.cleaned_data.get('data_nascimento')
    
        # Verificar se a data foi fornecida
        if not data_nascimento:
            raise ValidationError('Data de nascimento é obrigatória')
    
        hoje = date.today()
    
        # Verificar se a data não é no futuro
        if data_nascimento > hoje:
            raise ValidationError('Data de nascimento não pode ser no futuro')
    
        # Calcular idade de forma segura
        idade = hoje.year - data_nascimento.year
    
        # Ajustar se ainda não fez aniversário este ano
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
    username = forms.CharField(
        widget=forms.TextInput(attrs={
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

class EditarPerfilForm(forms.Form):
    nome = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu nome completo'
        }),
        label='Nome Completo'
    )
    
    email = forms.EmailField(
        max_length=100,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu@email.com'
        }),
        label='E-mail'
    )
    
    telemovel = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+351 123 456 789'
        }),
        label='Telefone'
    )
    
    data_nascimento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Data de Nascimento'
    )
    
    bairro = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu bairro'
        }),
        label='Bairro'
    )
    
    cidade = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sua cidade'
        }),
        label='Cidade'
    )
    
    provincia = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sua província'
        }),
        label='Província'
    )
    
    municipio = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu município'
        }),
        label='Município'
    )
    
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
            User = get_user_model()
            user = getattr(self, 'user_instance', None)
            if user and User.objects.filter(email=email).exclude(id=user.id).exists():
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
            if nova_senha != confirmar_senha:
                self.add_error('confirmar_senha', 'As senhas não coincidem.')

        return cleaned_data

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)
        
        if self.user_instance:
            self.fields['nome'].initial = self.user_instance.nome
            self.fields['email'].initial = self.user_instance.email
            self.fields['telemovel'].initial = self.user_instance.telemovel
            self.fields['data_nascimento'].initial = self.user_instance.data_nascimento
            self.fields['bairro'].initial = self.user_instance.bairro
            self.fields['cidade'].initial = self.user_instance.cidade
            self.fields['provincia'].initial = self.user_instance.provincia
            self.fields['municipio'].initial = self.user_instance.municipio

class AvatarForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
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

        # Validações
        max_size = 5 * 1024 * 1024  # 5MB
        if foto_perfil.size > max_size:
            raise ValidationError('A imagem deve ter no máximo 5MB.')

        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(foto_perfil.name)[1].lower()
        if ext not in valid_extensions:
            raise ValidationError('Formato não suportado. Use JPG, PNG ou GIF.')

        return foto_perfil