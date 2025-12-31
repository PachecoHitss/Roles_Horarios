from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import urllib.parse

def enviar_notificacion_programacion(usuario, asignaciones):
    """
    Envía un correo electrónico con las asignaciones de la semana
    y genera el texto para WhatsApp.
    """
    subject = 'Nueva Programación de Turnos'
    
    # Contexto para el template de correo
    context = {
        'usuario': usuario,
        'asignaciones': asignaciones,
    }
    
    html_message = render_to_string('users/email_programacion.html', context)
    plain_message = strip_tags(html_message)
    
    # Enviar Correo (Si SMTP está configurado)
    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error enviando correo a {usuario.email}: {e}")

def generar_link_whatsapp(usuario, asignaciones):
    """
    Genera un link de WhatsApp con el mensaje pre-formateado.
    """
    mensaje = f"Hola {usuario.first_name}, tu programación para esta semana es:\n\n"
    
    for asignacion in asignaciones:
        dia = asignacion.turno.get_dia_display()
        hora = f"{asignacion.turno.hora_inicio.strftime('%H:%M')} - {asignacion.turno.hora_fin.strftime('%H:%M')}"
        rol = asignacion.rol.nombre
        mensaje += f"📅 {dia} ({asignacion.turno.nombre})\n⏰ {hora}\n👤 Rol: {rol}\n\n"
    
    mensaje += "Por favor confirma tu asistencia. ¡Bendiciones!"
    
    # Codificar para URL
    mensaje_encoded = urllib.parse.quote(mensaje)
    
    # Si tiene celular, usarlo, si no, dejar vacío para que el admin lo ponga
    celular = usuario.celular if usuario.celular else ""
    
    return f"https://wa.me/{celular}?text={mensaje_encoded}"
