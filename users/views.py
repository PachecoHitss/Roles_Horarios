from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Turno, Disponibilidad, Rol, Programacion
from .notificaciones import generar_link_whatsapp

@login_required
def gestionar_disponibilidad(request):
    # Obtener los roles del usuario actual
    roles_usuario = request.user.roles.all()
    
    # Si el usuario no tiene roles, no puede definir disponibilidad
    if not roles_usuario.exists():
        messages.warning(request, "No tienes roles asignados para definir disponibilidad.")
        return redirect('home')

    # Obtener todos los turnos posibles para los roles del usuario
    # Usamos distinct() porque un turno podría aplicar a varios de sus roles
    turnos_posibles = Turno.objects.filter(roles_validos__in=roles_usuario).distinct().order_by('dia', 'hora_inicio')
    
    # Obtener disponibilidades ya marcadas
    disponibilidades_actuales = Disponibilidad.objects.filter(usuario=request.user).values_list('turno_id', flat=True)

    if request.method == 'POST':
        # Obtener lista de IDs de turnos seleccionados
        turnos_seleccionados_ids = request.POST.getlist('turnos')
        
        # Convertir a enteros para comparar
        turnos_seleccionados_ids = [int(id) for id in turnos_seleccionados_ids]
        
        # 1. Eliminar disponibilidades que ya no están seleccionadas
        Disponibilidad.objects.filter(usuario=request.user).exclude(turno_id__in=turnos_seleccionados_ids).delete()
        
        # 2. Crear nuevas disponibilidades
        nuevas_disponibilidades = []
        for turno_id in turnos_seleccionados_ids:
            if turno_id not in disponibilidades_actuales:
                nuevas_disponibilidades.append(Disponibilidad(usuario=request.user, turno_id=turno_id))
        
        if nuevas_disponibilidades:
            Disponibilidad.objects.bulk_create(nuevas_disponibilidades)
            
        messages.success(request, "Tu disponibilidad ha sido actualizada correctamente.")
        return redirect('disponibilidad')

    # Agrupar turnos por día para la vista
    turnos_por_dia = {}
    for turno in turnos_posibles:
        dia_nombre = turno.get_dia_display()
        if dia_nombre not in turnos_por_dia:
            turnos_por_dia[dia_nombre] = []
        turnos_por_dia[dia_nombre].append(turno)

    context = {
        'turnos_por_dia': turnos_por_dia,
        'disponibilidades_actuales': disponibilidades_actuales
    }
    return render(request, 'users/disponibilidad.html', context)

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
        lista_links.append({
            'usuario': usuario,
            'link': link,
            'asignaciones': lista_asignaciones
        })
    
    context = {
        'programacion': programacion,
        'lista_links': lista_links
    }
    return render(request, 'users/whatsapp_links.html', context)


