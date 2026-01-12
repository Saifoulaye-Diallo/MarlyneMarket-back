from django.core.management.base import BaseCommand
from apps.orders.models import EmailLog


class Command(BaseCommand):
    help = 'Affiche l\'historique des emails envoyés'

    def handle(self, *args, **options):
        logs = EmailLog.objects.all().order_by('-sent_at')
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(f'HISTORIQUE DES EMAILS ENVOYÉS')
        self.stdout.write('='*70)
        self.stdout.write(f'\nTotal d\'emails enregistrés: {logs.count()}\n')
        
        if logs.exists():
            self.stdout.write('\nDerniers emails:\n')
            for log in logs[:10]:
                status_color = {
                    'sent': self.style.SUCCESS,
                    'failed': self.style.ERROR,
                    'pending': self.style.WARNING
                }.get(log.status, self.style.NOTICE)
                
                self.stdout.write(f'• {log.sent_at.strftime("%Y-%m-%d %H:%M:%S")}')
                self.stdout.write(f'  Status: {status_color(log.status.upper())}')
                self.stdout.write(f'  Commande: {log.order.reference}')
                self.stdout.write(f'  Destinataire: {log.recipient}')
                self.stdout.write(f'  Sujet: {log.subject}')
                
                if log.error_message:
                    self.stdout.write(self.style.ERROR(f'  Erreur: {log.error_message[:100]}'))
                
                self.stdout.write('')
        else:
            self.stdout.write(self.style.WARNING('  Aucun email enregistré pour le moment'))
        
        self.stdout.write('='*70 + '\n')
