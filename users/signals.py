from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import CustomUser

@receiver(m2m_changed, sender=CustomUser.roles.through)
def actualizar_staff_status(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Actualiza el estado is_staff del usuario basado en sus roles.
    Si tiene el rol 'PULPITO' o 'COORDINADOR', se vuelve staff automáticamente.
    """
    if action in ["post_add", "post_remove", "post_clear"]:
        # Si es reverse (cambio en Rol.usuarios), instance es un Rol
        # Si no es reverse (cambio en User.roles), instance es un User
        
        if reverse:
            # El cambio fue desde el Rol, instance es el Rol
            # Esto es más complejo porque afecta a varios usuarios.
            # Por simplicidad, nos enfocamos en la asignación desde el Usuario.
            pass
        else:
            # El cambio fue desde el Usuario, instance es el Usuario
            user = instance
            roles_nombres = list(user.roles.values_list('nombre', flat=True))
            
            roles_admin = ['PULPITO', 'COORDINADOR']
            
            es_admin = any(rol.upper() in roles_admin for rol in roles_nombres)
            
            if es_admin and not user.is_staff:
                user.is_staff = True
                user.save()
                print(f"Usuario {user.email} promovido a Staff por rol administrativo.")
            
            # Opcional: Quitar staff si ya no tiene los roles (con cuidado de no quitar a superusers)
            # if not es_admin and user.is_staff and not user.is_superuser:
            #     user.is_staff = False
            #     user.save()
