# management/commands/corrigir_carrinhos_duplicados.py
from django.core.management.base import BaseCommand
from carinho.models import Carrinho
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Corrige carrinhos duplicados para usuários'
    
    def handle(self, *args, **options):
        usuarios_com_duplicados = User.objects.annotate(
            num_carrinhos_abertos=models.Count(
                'carrinho',
                filter=models.Q(carrinho__estado='aberto')
            )
        ).filter(num_carrinhos_abertos__gt=1)
        
        for usuario in usuarios_com_duplicados:
            self.stdout.write(f'Corrigindo carrinhos para {usuario.username}...')
            
            carrinhos_abertos = Carrinho.objects.filter(
                usuario=usuario,
                estado='aberto'
            ).order_by('-data_criacao')
            
            # Mantém o carrinho mais recente
            carrinho_principal = carrinhos_abertos.first()
            
            # Fecha os carrinhos antigos
            carrinhos_abertos.exclude(id=carrinho_principal.id).update(estado='fechado')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ {usuario.username}: mantido carrinho #{carrinho_principal.id}, '
                    f'fechados {carrinhos_abertos.count() - 1} carrinhos antigos'
                )
            )