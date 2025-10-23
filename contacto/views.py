from django.views.decorators.cache import cache_page
from celery import shared_task
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.generic import FormView
from django.db import transaction
import re
from .forms import ContactoForm
from .models import Contacto

# Compilar regex uma vez para reutilizar
PHONE_CLEANER = re.compile(r'\D')

class ContactoView(FormView):
    template_name = 'contact.html'
    form_class = ContactoForm
    success_url = 'sucesso/'
    
    @transaction.atomic
    def form_valid(self, form):
        """Processa o formulário válido de forma otimizada"""
        try:
            # Salvar o contacto na base de dados
            contacto = form.save(commit=False)
            
            # Limpar o telemóvel antes de salvar
            if contacto.telemovel:
                contacto.telemovel = PHONE_CLEANER.sub('', contacto.telemovel)
            
            contacto.save()
            
            # Enviar email de forma assíncrona (não bloqueante)
            self.enviar_email_async(contacto)
            
            messages.success(
                self.request, 
                'Mensagem enviada com sucesso! Entraremos em contacto brevemente.'
            )
            
            return super().form_valid(form)
            
        except Exception as e:
            # Log apropriado em produção
            messages.error(
                self.request,
                'Ocorreu um erro ao processar o seu pedido. Tente novamente.'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Por favor, corrija os erros abaixo.'
        )
        return super().form_invalid(form)
    
    def enviar_email_async(self, contacto):
        """Envia email de forma não bloqueante"""
        try:
            from threading import Thread
            
            def send_email_thread():
                try:
                    self._enviar_email_notificacao(contacto)
                except Exception as e:
                    # Log do erro sem afetar o usuário
                    print(f"Erro ao enviar email: {e}")
            
            # Iniciar thread para envio de email
            thread = Thread(target=send_email_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            print(f"Erro ao iniciar thread de email: {e}")
    
    def _enviar_email_notificacao(self, contacto):
        """Método interno para enviar email"""
        subject = f'Novo Contacto: {contacto.assunto}'
        message = f'''
Novo contacto recebido:

Nome: {contacto.nome}
E-mail: {contacto.email}
Telemóvel: {contacto.telemovel}
Assunto: {contacto.get_assunto_display()}
Mensagem: {contacto.mensagem}

Data: {contacto.data_envio}
'''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.CONTACT_EMAIL],
            fail_silently=True,  # Não levantar exceção em produção
        )

def contacto_sucesso(request):
    """View simples de sucesso com cache"""
    return render(request, 'sucesso.html')

# Versão otimizada com função-based view
def contacto_view(request):
    """View baseada em função otimizada"""
    if request.method == 'POST':
        form = ContactoForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    contacto = form.save(commit=False)
                    
                    # Processar telemóvel
                    if contacto.telemovel:
                        contacto.telemovel = PHONE_CLEANER.sub('', contacto.telemovel)
                    
                    contacto.save()
                    
                    # Email assíncrono
                    enviar_email_async(contacto)
                    
                    messages.success(request, 'Mensagem enviada com sucesso!')
                    return redirect('contacto_sucesso')
                    
            except Exception as e:
                messages.error(request, 'Erro ao processar o formulário. Tente novamente.')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = ContactoForm()
    
    return render(request, 'contact.html', {'form': form})

def enviar_email_async(contacto):
    """Função auxiliar para envio assíncrono de email"""
    try:
        from threading import Thread
        
        def send_email():
            try:
                _enviar_email(contacto)
            except Exception as e:
                print(f"Erro ao enviar email: {e}")
        
        thread = Thread(target=send_email)
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        print(f"Erro ao iniciar thread: {e}")

def _enviar_email(contacto):
    """Função interna para envio de email"""
    subject = f'Novo Contacto: {contacto.assunto}'
    message = f'''
Novo contacto recebido:

Nome: {contacto.nome}
E-mail: {contacto.email}
Telemóvel: {contacto.telemovel}
Assunto: {contacto.get_assunto_display()}
Mensagem: {contacto.mensagem}

Data: {contacto.data_envio}
'''
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.CONTACT_EMAIL],
        fail_silently=True,
    )

@cache_page(60 * 15)  # Cache de 15 minutos
def contacto_sucesso(request):
    return render(request, 'sucesso.html')

@shared_task
def enviar_email_contacto(contacto_id):
    contacto = Contacto.objects.get(id=contacto_id)
    # código do email...