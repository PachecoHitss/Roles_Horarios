import random
from datetime import timedelta
from django.db import transaction
from .models import Asignacion, Disponibilidad, Turno, Rol

class AlgoritmoProgramacion:
    def __init__(self, programacion):
        self.programacion = programacion
        self.fecha_inicio = programacion.fecha_inicio
        self.fecha_fin = programacion.fecha_fin

    def ejecutar(self):
        # Limpiar asignaciones previas de esta programación para evitar duplicados
        self.programacion.asignaciones.all().delete()
        
        dias_semana = []
        delta = self.fecha_fin - self.fecha_inicio
        for i in range(delta.days + 1):
            fecha = self.fecha_inicio + timedelta(days=i)
            dias_semana.append(fecha)

        with transaction.atomic():
            for fecha in dias_semana:
                dia_semana_num = fecha.weekday() # 0=Lunes, 6=Domingo
                
                # Obtener turnos de este día
                turnos_dia = Turno.objects.filter(dia=dia_semana_num)
                
                for turno in turnos_dia:
                    self.asignar_turno(fecha, turno)

    def asignar_turno(self, fecha, turno):
        # Roles que aplican a este turno
        roles_necesarios = turno.roles_validos.all()
        
        for rol in roles_necesarios:
            # Buscar candidatos disponibles
            # 1. Que tengan el rol
            # 2. Que hayan marcado disponibilidad para este turno específico
            candidatos = Disponibilidad.objects.filter(
                turno=turno,
                usuario__roles=rol
            ).select_related('usuario')
            
            lista_candidatos = [d.usuario for d in candidatos]
            
            # Filtrar candidatos que ya tienen asignación ese día en otro turno (opcional, según reglas)
            # Aquí asumimos que pueden servir en AM y PM si marcaron disponibilidad, 
            # pero NO en el mismo turno con otro rol (validado por unique_together en modelo)
            
            # Lógica de Parejas (Dependencia)
            # Si seleccionamos a alguien con pareja, intentamos asignar a su pareja también si es posible
            
            # Mezclar para aleatoriedad básica (equidad simple)
            random.shuffle(lista_candidatos)
            
            # Seleccionar (Aquí definimos CUÁNTOS por rol. Por ahora 1 por rol por turno como base)
            # TODO: Definir cupos por rol en el futuro. Asumimos 2 personas por rol por turno.
            cupos = 2 
            asignados_count = 0
            
            for usuario in lista_candidatos:
                if asignados_count >= cupos:
                    break
                
                # Verificar si ya está asignado en este turno con otro rol
                if Asignacion.objects.filter(programacion=self.programacion, fecha=fecha, turno=turno, usuario=usuario).exists():
                    continue

                # Crear asignación
                Asignacion.objects.create(
                    programacion=self.programacion,
                    usuario=usuario,
                    turno=turno,
                    rol=rol,
                    fecha=fecha
                )
                asignados_count += 1
                
                # Manejo de Pareja
                if usuario.pareja:
                    pareja = usuario.pareja
                    # Verificar si la pareja es candidata (tiene rol y disponibilidad)
                    es_candidato_pareja = any(u == pareja for u in lista_candidatos)
                    
                    if es_candidato_pareja and asignados_count < cupos:
                         if not Asignacion.objects.filter(programacion=self.programacion, fecha=fecha, turno=turno, usuario=pareja).exists():
                            Asignacion.objects.create(
                                programacion=self.programacion,
                                usuario=pareja,
                                turno=turno,
                                rol=rol, # Asumimos mismo rol, o habría que buscar qué rol tiene la pareja
                                fecha=fecha
                            )
                            asignados_count += 1
