from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import ModeloAuditable, Area
from apps.usuarios.models import Usuario
from apps.bienes.models import Bien


class MovimientoBien(ModeloAuditable):
    """
    Historial de movimientos de un bien.
    Registra asignaciones, transferencias, devoluciones y bajas.
    """
    TIPO_CHOICES = [
        ('ASIGNACION', 'Asignación Inicial'),
        ('TRANSFERENCIA', 'Transferencia Interna'),
        ('DEVOLUCION', 'Devolución'),
        ('BAJA', 'Baja'),
    ]

    bien = models.ForeignKey(
        Bien,
        on_delete=models.CASCADE,
        related_name="movimientos",
        verbose_name="Bien"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Movimiento"
    )

    # ========== ORIGEN ==========
    area_origen = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_origen",
        verbose_name="Área de Origen"
    )
    usuario_origen = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_origen",
        verbose_name="Usuario de Origen"
    )

    # ========== DESTINO ==========
    area_destino = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_destino",
        verbose_name="Área de Destino"
    )
    usuario_destino = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_destino",
        verbose_name="Usuario de Destino"
    )

    # ========== METADATOS DEL MOVIMIENTO ==========
    fecha_movimiento = models.DateTimeField(
        verbose_name="Fecha del Movimiento"
    )
    documento_autorizacion = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Documento de Autorización"
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # ========== REGISTRO EN EL SISTEMA ==========
    registrado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="movimientos_registrados",
        verbose_name="Registrado por"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro en Sistema"
    )

    class Meta:
        verbose_name = "Movimiento de Bien"
        verbose_name_plural = "Movimientos de Bienes"
        ordering = ['-fecha_movimiento']

    def clean(self):
        super().clean()

        # 1. Validación para TRANSFERENCIA
        if self.tipo == 'TRANSFERENCIA':
            if not self.area_destino or not self.usuario_destino:
                raise ValidationError({
                    'area_destino': 'Una transferencia requiere especificar el Área y Usuario de destino.'
                })
            if self.area_origen == self.area_destino and self.usuario_origen == self.usuario_destino:
                raise ValidationError(
                    'El área y usuario de destino no pueden ser idénticos al origen actual.'
                )

        # 2. Validación para BAJA
        elif self.tipo == 'BAJA':
            if self.area_destino or self.usuario_destino:
                raise ValidationError(
                    'Un movimiento de BAJA no debe registrar un área ni usuario de destino.'
                )

        # 3. Validación para ASIGNACIÓN INICIAL
        elif self.tipo == 'ASIGNACION':
            if not self.area_destino or not self.usuario_destino:
                raise ValidationError({
                    'area_destino': 'La asignación inicial requiere un Área y Usuario de destino.'
                })

    def save(self, *args, **kwargs):
        # Ejecuta siempre la validación clean() antes de guardar en DB (incluso desde el admin/shell)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.bien.codigo_patrimonial} - {self.tipo} ({self.fecha_movimiento.strftime('%d/%m/%Y')})"