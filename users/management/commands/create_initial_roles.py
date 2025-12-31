from django.core.management.base import BaseCommand
from users.models import Rol

class Command(BaseCommand):
    help = 'Creates initial roles'

    def handle(self, *args, **options):
        roles = [
            "ACOMODACION",
            "BIENVENIDA",
            "ASEO",
            "SONIDO",
            "BAÑOS",
            "CASILLEROS",
            "LOGISTICA ACOMODACION Y BIENVENIDA",
            "OFRENDA",
            "PULPITO"
        ]

        for nombre in roles:
            rol, created = Rol.objects.get_or_create(nombre=nombre)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Rol "{nombre}" creado.'))
            else:
                self.stdout.write(self.style.WARNING(f'Rol "{nombre}" ya existe.'))
