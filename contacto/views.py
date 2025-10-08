from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.generic import FormView
from .forms import ContactoForm
from .models import Contacto

class ContactoView(FormView):
    template_name = 'contact.html'
    form_class = ContactoForm
    success_url = 'sucesso/'
    
    def form_valid(self, form):
        # Salvar o contacto na base de dados
        contacto = form.save(commit=False)
        
        # Limpar o telemóvel antes de salvar (opcional)
        if contacto.telemovel:
            import re
            contacto.telemovel = re.sub(r'\D', '', contacto.telemovel)
        
        contacto.save()
        
        # Enviar email de notificação (opcional)
        self.enviar_email_notificacao(contacto)
        
        messages.success(
            self.request, 
            'Mensagem enviada com sucesso! Entraremos em contacto brevemente.'
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Por favor, corrija os erros abaixo.'
        )
        return super().form_invalid(form)
    
    def enviar_email_notificacao(self, contacto):
        """Envia email de notificação para a equipa"""
        try:
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
                [settings.CONTACT_EMAIL],  # Definir no settings.py
                fail_silently=False,
            )
        except Exception as e:
            # Log do erro sem interromper o processo
            print(f"Erro ao enviar email: {e}")

def contacto_sucesso(request):
    return render(request, 'sucesso.html')

# Versão alternativa com função-based view
def contacto_view(request):
    if request.method == 'POST':
        form = ContactoForm(request.POST)
        if form.is_valid():
            contacto = form.save(commit=False)
            
            # Processar telemóvel
            if contacto.telemovel:
                import re
                contacto.telemovel = re.sub(r'\D', '', contacto.telemovel)
            
            contacto.save()
            
            messages.success(request, 'Mensagem enviada com sucesso!')
            return redirect('contacto_sucesso')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = ContactoForm()
    
    return render(request, 'contacto/contacto.html', {'form': form})