from django.db import models
from django.conf import settings
from apps.core.models import Area
from apps.bienes.models import Bien

class SesionInventario(models.Model):
    ESTADOS = (
        ('EN_PROCESO', 'En Proceso'),
        ('FINALIZADO', 'Finalizado / Acta Generada'),
    )

    area = models.ForeignKey(Area, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Área")
    custodio = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sesiones_inventario')
    realizado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inventarios_realizados')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='EN_PROCESO')
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Inventario #{self.id} - {self.custodio.get_full_name()} ({self.get_estado_display()})"


class DetalleInventario(models.Model):
    ESTADOS_HALLAZGO = (
        ('VERIFICADO', 'Verificado / Presente'),
        ('NO_LOCALIZADO', 'No Localizado / Faltante'),
        ('MAL_ESTADO', 'Dañado / Con Observación'),
    )

    sesion = models.ForeignKey(SesionInventario, on_delete=models.CASCADE, related_name='detalles')
    bien = models.ForeignKey(Bien, on_delete=models.CASCADE)
    verificado = models.BooleanField(default=False)
    estado_hallazgo = models.CharField(max_length=20, choices=ESTADOS_HALLAZGO, default='NO_LOCALIZADO')
    fecha_escaneo = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('sesion', 'bien')