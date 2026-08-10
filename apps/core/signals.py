# apps/core/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import ModeloAuditable
from .middleware import get_current_user

@receiver(pre_save)
def set_audit_fields(sender, instance, **kwargs):
    """
    Señal que asigna automáticamente creado_por y modificado_por
    a cualquier modelo que herede de ModeloAuditable.
    """
    if not isinstance(instance, ModeloAuditable):
        return  # Solo actuar sobre modelos auditables

    user = get_current_user()
    if user and not user.is_anonymous:
        if instance.pk is None:  # Creación
            instance.creado_por = user
        # Siempre actualizar modificado_por (incluso en creación, aunque sea redundante)
        instance.modificado_por = user