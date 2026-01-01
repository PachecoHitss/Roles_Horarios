from django.core.management.base import BaseCommand
from users.models import CustomUser

class Command(BaseCommand):
    help = 'Actualiza usuarios con rol PULPITO para ser staff'

    def handle(self, *args, **options):
        users = CustomUser.objects.filter(roles__nombre__iexact='PULPITO', is_staff=False)
        count = users.count()
        
        for user in users:
            user.is_staff = True
            user.save()
            self.stdout.write(f'Usuario {user.email} actualizado a Staff.')
            
        self.stdout.write(self.style.SUCCESS(f'Se actualizaron {count} usuarios con rol PULPITO.'))
