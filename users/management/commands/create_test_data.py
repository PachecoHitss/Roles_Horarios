from django.core.management.base import BaseCommand
from users.models import CustomUser, Rol, Turno, Indisponibilidad
import random

class Command(BaseCommand):
    help = 'Creates dummy data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos de prueba...')

        # 1. Crear Superusuario (Admin)
        if not CustomUser.objects.filter(email='admin@prueba.com').exists():
            CustomUser.objects.create_superuser(
                email='admin@prueba.com',
                password='admin',
                first_name='Administrador',
                last_name='Principal',
                documento='123456789',
                celular='3001234567'
            )
            self.stdout.write(self.style.SUCCESS('Superusuario creado: admin@prueba.com / admin'))

        # 2. Crear Usuarios Voluntarios
        nombres = ['Juan', 'Maria', 'Pedro', 'Ana', 'Luis', 'Sofia', 'Carlos', 'Laura', 'Jose', 'Marta']
        apellidos = ['Perez', 'Gomez', 'Rodriguez', 'Lopez', 'Martinez', 'Garcia', 'Hernandez', 'Diaz', 'Torres', 'Ramirez']
        
        roles_db = list(Rol.objects.all())
        turnos_db = list(Turno.objects.all())

        usuarios_creados = []

        for i in range(10):
            email = f'usuario{i+1}@prueba.com'
            if not CustomUser.objects.filter(email=email).exists():
                user = CustomUser.objects.create_user(
                    email=email,
                    password=f'doc{i+1}', # Contraseña = documento
                    documento=f'doc{i+1}',
                    first_name=nombres[i],
                    last_name=apellidos[i],
                    celular=f'300000000{i}',
                    genero=random.choice(['M', 'F']),
                    bes=random.choice([True, False]),
                    im=random.choice([True, False]),
                    pf=random.choice([True, False])
                )
                
                # Asignar Roles aleatorios (1 a 3 roles por persona)
                roles_asignados = random.sample(roles_db, k=random.randint(1, 3))
                user.roles.set(roles_asignados)
                user.save()
                usuarios_creados.append(user)
                
                # Crear Indisponibilidad Aleatoria (Simular que NO pueden en el 20% de los turnos)
                turnos_posibles = Turno.objects.filter(roles_validos__in=roles_asignados).distinct()
                for turno in turnos_posibles:
                    if random.random() < 0.2: # 20% de probabilidad de NO poder
                        Indisponibilidad.objects.get_or_create(usuario=user, turno=turno)

        self.stdout.write(self.style.SUCCESS(f'{len(usuarios_creados)} usuarios voluntarios creados con roles y disponibilidad.'))

        # 3. Crear Pareja de prueba
        if len(usuarios_creados) >= 2:
            u1 = usuarios_creados[0]
            u2 = usuarios_creados[1]
            u1.pareja = u2
            u1.save()
            u2.pareja = u1 # Relación bidireccional manual para prueba
            u2.save()
            self.stdout.write(self.style.SUCCESS(f'Pareja creada: {u1} y {u2}'))
