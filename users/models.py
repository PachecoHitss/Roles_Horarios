from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager

# Importamos los modelos de programación al final para evitar importaciones circulares si fuera necesario,
# pero aquí los definiremos en archivos separados y los importaremos en __init__.py o admin.py


class Rol(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    # Campos personalizados
    documento = models.CharField(max_length=20, unique=True, verbose_name="Documento de Identidad")
    celular = models.CharField(max_length=20, verbose_name="Celular")
    
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, verbose_name="Género")
    
    # Campos booleanos específicos
    bes = models.BooleanField(default=False, verbose_name="B.E.S")
    im = models.BooleanField(default=False, verbose_name="I.M")
    pf = models.BooleanField(default=False, verbose_name="PF")

    # Relación con Roles (Un usuario puede tener varios roles)
    roles = models.ManyToManyField(Rol, related_name='usuarios', blank=True)
    
    # Dependencia de horario (Pareja)
    pareja = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Pareja / Dependencia", help_text="Usuario con el que debe coincidir obligatoriamente en turno")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['documento', 'first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

class Turno(models.Model):
    DIAS = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    dia = models.IntegerField(choices=DIAS, verbose_name="Día de la semana")
    nombre = models.CharField(max_length=50, verbose_name="Nombre del Turno") # Ej: AM, PM, AM1
    hora_inicio = models.TimeField(verbose_name="Hora Inicio")
    hora_fin = models.TimeField(verbose_name="Hora Fin")
    
    # Relación para saber a qué roles aplica este turno
    roles_validos = models.ManyToManyField(Rol, related_name='turnos_disponibles', blank=True)

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        ordering = ['dia', 'hora_inicio']

    def __str__(self):
        return f"{self.get_dia_display()} - {self.nombre} ({self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')})"

class Indisponibilidad(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='indisponibilidades')
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name='usuarios_indisponibles')
    
    class Meta:
        verbose_name = "Indisponibilidad (Excepción)"
        verbose_name_plural = "Indisponibilidades"
        unique_together = ('usuario', 'turno')

    def __str__(self):
        return f"{self.usuario} NO PUEDE en {self.turno}"

# Modelos de Programación
class Programacion(models.Model):
    fecha_inicio = models.DateField(verbose_name="Fecha Inicio Semana")
    fecha_fin = models.DateField(verbose_name="Fecha Fin Semana")
    publicada = models.BooleanField(default=False, verbose_name="Publicada")
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Programación Semanal"
        verbose_name_plural = "Programaciones Semanales"
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"Semana del {self.fecha_inicio} al {self.fecha_fin}"

class Asignacion(models.Model):
    programacion = models.ForeignKey(Programacion, on_delete=models.CASCADE, related_name='asignaciones')
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='asignaciones')
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE) # El rol que ejercerá en ese turno
    fecha = models.DateField(verbose_name="Fecha del Turno")
    
    class Meta:
        verbose_name = "Asignación de Turno"
        verbose_name_plural = "Asignaciones de Turno"
        unique_together = ('usuario', 'fecha', 'turno') # Un usuario no puede tener 2 roles en el mismo turno/fecha

    def __str__(self):
        return f"{self.usuario} - {self.rol} - {self.fecha} ({self.turno.nombre})"


