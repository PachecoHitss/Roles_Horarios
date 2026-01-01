from django.contrib import admin, messages
from django.utils.html import format_html
from .models import CustomUser, Rol, Turno, Indisponibilidad, Programacion, Asignacion
from .algoritmo import AlgoritmoProgramacion
from .notificaciones import enviar_notificacion_programacion, generar_link_whatsapp

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'documento', 'celular', 'pareja', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'documento')
    list_filter = ('is_staff', 'is_active', 'bes', 'im', 'pf', 'roles')
    autocomplete_fields = ['pareja']

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('get_dia_display', 'nombre', 'hora_inicio', 'hora_fin')
    list_filter = ('dia',)
    search_fields = ('nombre',)
    filter_horizontal = ('roles_validos',)

@admin.register(Indisponibilidad)
class IndisponibilidadAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'turno')
    list_filter = ('usuario', 'turno__dia')
    autocomplete_fields = ['usuario', 'turno']

class AsignacionInline(admin.TabularInline):
    model = Asignacion
    extra = 0
    autocomplete_fields = ['usuario', 'turno', 'rol']

@admin.register(Programacion)
class ProgramacionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'publicada', 'creada_en', 'acciones_notificacion')
    list_filter = ('publicada',)
    inlines = [AsignacionInline]
    actions = ['generar_programacion_automatica', 'publicar_y_notificar']

    def generar_programacion_automatica(self, request, queryset):
        for programacion in queryset:
            algoritmo = AlgoritmoProgramacion(programacion)
            algoritmo.ejecutar()
            messages.success(request, f"Programación generada exitosamente para: {programacion}")
    generar_programacion_automatica.short_description = "Generar asignaciones automáticas"

    def publicar_y_notificar(self, request, queryset):
        for programacion in queryset:
            programacion.publicada = True
            programacion.save()
            
            # Agrupar asignaciones por usuario
            asignaciones = programacion.asignaciones.all().select_related('usuario', 'turno', 'rol')
            usuarios_afectados = {}
            
            for asignacion in asignaciones:
                if asignacion.usuario not in usuarios_afectados:
                    usuarios_afectados[asignacion.usuario] = []
                usuarios_afectados[asignacion.usuario].append(asignacion)
            
            # Enviar correos
            count = 0
            for usuario, lista_asignaciones in usuarios_afectados.items():
                enviar_notificacion_programacion(usuario, lista_asignaciones)
                count += 1
            
            messages.success(request, f"Programación publicada. Se enviaron {count} correos de notificación.")
    publicar_y_notificar.short_description = "Publicar y Enviar Correos"

    def acciones_notificacion(self, obj):
        return format_html(
            '<a class="button" href="{}">Ver Links WhatsApp</a>',
            f"/users/whatsapp-links/{obj.id}/"
        )
    acciones_notificacion.short_description = "WhatsApp"

@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol', 'fecha', 'turno', 'programacion')
    list_filter = ('programacion', 'rol', 'turno__dia')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'usuario__email')

