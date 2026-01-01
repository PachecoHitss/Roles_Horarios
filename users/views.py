from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Turno, Indisponibilidad, Rol, Programacion, Asignacion
from .notificaciones import generar_link_whatsapp, enviar_notificacion_programacion, generar_mensaje_whatsapp

def home(request):
    if request.user.is_authenticated:
        # Si es staff y NO tiene roles asignados (Admin puro), redirigir a gestión
        if request.user.is_staff and not request.user.roles.exists():
            return redirect('lista_programaciones')
    return render(request, 'home.html')

@login_required
def gestionar_disponibilidad(request):
    # Obtener los roles del usuario actual
    roles_usuario = request.user.roles.all()
    
    # Si el usuario no tiene roles, no puede definir disponibilidad
    if not roles_usuario.exists():
        messages.warning(request, "No tienes roles asignados para definir disponibilidad.")
        return redirect('home')

    # Obtener todos los turnos posibles para los roles del usuario
    turnos_posibles = Turno.objects.filter(roles_validos__in=roles_usuario).distinct().order_by('dia', 'hora_inicio')
    
    # Obtener indisponibilidades ya marcadas (turnos donde NO puede)
    indisponibilidades_actuales = Indisponibilidad.objects.filter(usuario=request.user).values_list('turno_id', flat=True)

    if request.method == 'POST':
        # Obtener lista de IDs de turnos seleccionados (los que NO puede)
        turnos_no_puede_ids = request.POST.getlist('turnos')
        
        # Convertir a enteros
        turnos_no_puede_ids = [int(id) for id in turnos_no_puede_ids]
        
        # 1. Eliminar indisponibilidades que ya no están seleccionadas (ahora sí puede)
        Indisponibilidad.objects.filter(usuario=request.user).exclude(turno_id__in=turnos_no_puede_ids).delete()
        
        # 2. Crear nuevas indisponibilidades
        nuevas_indisponibilidades = []
        for turno_id in turnos_no_puede_ids:
            if turno_id not in indisponibilidades_actuales:
                nuevas_indisponibilidades.append(Indisponibilidad(usuario=request.user, turno_id=turno_id))
        
        if nuevas_indisponibilidades:
            Indisponibilidad.objects.bulk_create(nuevas_indisponibilidades)
            
        messages.success(request, "Tus excepciones se han guardado. Por favor revisa el resumen y confirma.")
        return redirect('resumen_disponibilidad')

    # Agrupar turnos por Conjunto de Roles y luego por Día
    # Estructura: [ {'roles': 'Acomodacion, Bienvenida', 'dias': {'Lunes': [t1, t2]}} ]
    
    roles_usuario_ids = set(roles_usuario.values_list('id', flat=True))
    grupos_map = {} # Key: tuple of role names, Value: dict of days
    
    # Optimización: Prefetch roles_validos para evitar N+1
    turnos_posibles = Turno.objects.filter(roles_validos__in=roles_usuario).distinct().prefetch_related('roles_validos').order_by('dia', 'hora_inicio')

    for turno in turnos_posibles:
        # Determinar para qué roles del usuario aplica este turno
        roles_aplicables = [r.nombre for r in turno.roles_validos.all() if r.id in roles_usuario_ids]
        roles_aplicables.sort()
        key_roles = tuple(roles_aplicables)
        
        if key_roles not in grupos_map:
            grupos_map[key_roles] = {}
            
        dia_nombre = turno.get_dia_display()
        if dia_nombre not in grupos_map[key_roles]:
            grupos_map[key_roles][dia_nombre] = []
        
        grupos_map[key_roles][dia_nombre].append(turno)

    # Convertir a lista para el template
    grupos_lista = []
    for roles_tuple, dias_dict in grupos_map.items():
        grupos_lista.append({
            'roles_str': ", ".join(roles_tuple),
            'dias': dias_dict
        })

    context = {
        'grupos_turnos': grupos_lista,
        'indisponibilidades_actuales': indisponibilidades_actuales
    }
    return render(request, 'users/disponibilidad.html', context)

@login_required
def resumen_disponibilidad(request):
    roles_usuario = request.user.roles.all()
    if not roles_usuario.exists():
        return redirect('home')

    # Obtener todos los turnos posibles
    turnos_posibles = Turno.objects.filter(roles_validos__in=roles_usuario).distinct().order_by('dia', 'hora_inicio')
    
    # Obtener IDs de indisponibilidades
    indisponibilidades_ids = Indisponibilidad.objects.filter(usuario=request.user).values_list('turno_id', flat=True)
    
    turnos_disponibles = []
    turnos_no_disponibles = []
    
    for turno in turnos_posibles:
        if turno.id in indisponibilidades_ids:
            turnos_no_disponibles.append(turno)
        else:
            turnos_disponibles.append(turno)
            
    context = {
        'turnos_disponibles': turnos_disponibles,
        'turnos_no_disponibles': turnos_no_disponibles,
    }
    return render(request, 'users/resumen_disponibilidad.html', context)

@user_passes_test(lambda u: u.is_staff)
def ver_links_whatsapp(request, programacion_id):
    programacion = get_object_or_404(Programacion, id=programacion_id)
    
    # Agrupar asignaciones por usuario
    asignaciones = programacion.asignaciones.all().select_related('usuario', 'turno', 'rol').order_by('usuario__first_name')
    usuarios_data = {}
    
    for asignacion in asignaciones:
        if asignacion.usuario not in usuarios_data:
            usuarios_data[asignacion.usuario] = []
        usuarios_data[asignacion.usuario].append(asignacion)
    
    lista_links = []
    for usuario, lista_asignaciones in usuarios_data.items():
        link = generar_link_whatsapp(usuario, lista_asignaciones)
        mensaje = generar_mensaje_whatsapp(usuario, lista_asignaciones)
        lista_links.append({
            'usuario': usuario,
            'link': link,
            'mensaje': mensaje,
            'asignaciones': lista_asignaciones
        })
    
    context = {
        'programacion': programacion,
        'lista_links': lista_links
    }
    return render(request, 'users/whatsapp_links.html', context)

@login_required
def mis_programaciones(request):
    # Obtener la última programación publicada
    programacion_actual = Programacion.objects.filter(publicada=True).order_by('-fecha_inicio').first()
    
    asignaciones = []
    if programacion_actual:
        asignaciones = Asignacion.objects.filter(
            programacion=programacion_actual, 
            usuario=request.user
        ).select_related('turno', 'rol').order_by('fecha', 'turno__hora_inicio')
        
    context = {
        'programacion': programacion_actual,
        'asignaciones': asignaciones
    }
    return render(request, 'users/mis_programaciones.html', context)

@user_passes_test(lambda u: u.is_staff)
def lista_programaciones(request):
    programaciones = Programacion.objects.all().order_by('-fecha_inicio')
    return render(request, 'users/lista_programaciones.html', {'programaciones': programaciones})

@user_passes_test(lambda u: u.is_staff)
def detalle_programacion(request, programacion_id):
    programacion = get_object_or_404(Programacion, id=programacion_id)
    asignaciones = programacion.asignaciones.all().select_related('usuario', 'turno', 'rol').order_by('fecha', 'turno__hora_inicio', 'rol__nombre')
    
    if request.method == 'POST' and 'publicar' in request.POST:
        programacion.publicada = True
        programacion.save()
        
        # Lógica de notificación
        usuarios_afectados = {}
        for asignacion in asignaciones:
            if asignacion.usuario not in usuarios_afectados:
                usuarios_afectados[asignacion.usuario] = []
            usuarios_afectados[asignacion.usuario].append(asignacion)
        
        count = 0
        for usuario, lista_asignaciones in usuarios_afectados.items():
            enviar_notificacion_programacion(usuario, lista_asignaciones)
            count += 1
            
        messages.success(request, f"Programación publicada exitosamente. Se enviaron {count} notificaciones.")
        return redirect('detalle_programacion', programacion_id=programacion.id)

    # Filtrado por Rol
    rol_filter = request.GET.get('rol')
    asignaciones_visual = asignaciones # Copia para filtrar sin afectar lógica de publicación si se moviera

    if rol_filter:
        if rol_filter == 'coordinacion':
            roles_coordinacion = ['ACOMODACION', 'BIENVENIDA', 'LOGISTICA ACOMODACION Y BIENVENIDA']
            asignaciones_visual = asignaciones_visual.filter(rol__nombre__in=roles_coordinacion)
        elif rol_filter.isdigit():
            asignaciones_visual = asignaciones_visual.filter(rol__id=int(rol_filter))

    # Agrupar asignaciones para la vista de cuadrícula
    # Estructura: Lista de objetos { 'fecha': date, 'turno': turno, 'roles': { 'RolName': [user1, user2] } }
    agenda_map = {}
    
    for asignacion in asignaciones_visual:
        key = (asignacion.fecha, asignacion.turno)
        if key not in agenda_map:
            agenda_map[key] = {
                'fecha': asignacion.fecha,
                'turno': asignacion.turno,
                'roles': {}
            }
        
        rol_nombre = asignacion.rol.nombre
        if rol_nombre not in agenda_map[key]['roles']:
            agenda_map[key]['roles'][rol_nombre] = []
            
        agenda_map[key]['roles'][rol_nombre].append(asignacion.usuario)
    
    # Ordenar por fecha y hora
    agenda_visual = sorted(agenda_map.values(), key=lambda x: (x['fecha'], x['turno'].hora_inicio))

    # Obtener lista de roles para el filtro
    roles = Rol.objects.all().order_by('nombre')

    context = {
        'programacion': programacion,
        'asignaciones': asignaciones_visual,
        'agenda_visual': agenda_visual,
        'roles': roles,
        'rol_filter': rol_filter
    }
    return render(request, 'users/detalle_programacion.html', context)




