from django.core.management.base import BaseCommand
from users.models import Rol, Turno
from datetime import time

class Command(BaseCommand):
    help = 'Creates initial shifts (turnos)'

    def handle(self, *args, **options):
        # Definición de horarios
        # Lunes (0) a Viernes (4)
        dias_semana = [0, 1, 2, 3, 4]
        # Sábado (5)
        # Domingo (6)

        # 1. Crear Turnos Generales (L-V)
        for dia in dias_semana:
            self.crear_turno(dia, "AM", time(6, 0), time(8, 0), general=True)
            self.crear_turno(dia, "PM", time(17, 0), time(20, 0), general=True)

        # 2. Crear Turnos Sábado
        self.crear_turno(5, "PM", time(16, 0), time(19, 0), general=True)
        
        # Turno Especial ASEO Sábado
        turno_aseo = self.crear_turno(5, "AM", time(7, 0), time(12, 0), general=False)
        rol_aseo = Rol.objects.filter(nombre="ASEO").first()
        if rol_aseo and turno_aseo:
            turno_aseo.roles_validos.add(rol_aseo)
            self.stdout.write(self.style.SUCCESS(f'Asignado rol ASEO a turno Sábado AM'))

        # 3. Crear Turnos Domingo
        self.crear_turno(6, "AM1", time(7, 0), time(10, 0), general=True)
        self.crear_turno(6, "AM2", time(10, 0), time(13, 0), general=True)

    def crear_turno(self, dia, nombre, inicio, fin, general=True):
        turno, created = Turno.objects.get_or_create(
            dia=dia,
            nombre=nombre,
            hora_inicio=inicio,
            hora_fin=fin
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Turno creado: {turno}'))
        else:
            self.stdout.write(f'Turno ya existe: {turno}')

        if general:
            # Asignar a todos los roles EXCEPTO ASEO
            roles_generales = Rol.objects.exclude(nombre="ASEO")
            turno.roles_validos.set(roles_generales)
        
        return turno
