import qrcode
import uuid
from io import BytesIO
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
from apps.core.models import ModeloAuditable, Sede, Area
from apps.usuarios.models import Usuario


class Bien(ModeloAuditable):
    # ========== IDENTIFICADORES ==========
    codigo_patrimonial = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Código Patrimonial"
    )
    codigo_interno = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="Código Interno"
    )

    # ========== DATOS DEL BIEN ==========
    denominacion = models.CharField(max_length=500, verbose_name="Denominación")
    marca = models.CharField(max_length=200, blank=True, null=True, verbose_name="Marca")
    modelo = models.CharField(max_length=200, blank=True, null=True, verbose_name="Modelo")
    serie = models.CharField(max_length=100, blank=True, null=True, verbose_name="Número de Serie")
    color = models.CharField(max_length=50, blank=True, null=True, verbose_name="Color")
    dimensiones = models.CharField(max_length=100, blank=True, null=True, verbose_name="Dimensiones")
    ubicacion_fisica = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Ubicación Física"
    )

    # ========== UBICACIÓN Y RESPONSABLE ==========
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, verbose_name="Sede")
    area = models.ForeignKey(Area, on_delete=models.PROTECT, verbose_name="Área")
    usuario_responsable = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="bienes_actuales",
        verbose_name="Usuario Responsable Actual"
    )

    # ========== ESTADO ==========
    ESTADO_CHOICES = [
        ('B', 'Bueno'),
        ('R', 'Regular'),
        ('M', 'Malo'),
        ('I', 'Inservible'),
        ('N', 'Nuevo'),
    ]
    estado_conservacion = models.CharField(
        max_length=1,
        choices=ESTADO_CHOICES,
        default='B',
        verbose_name="Estado de Conservación"
    )

    # ========== DATOS CONTABLES Y SIGA ==========
    catalogo_siga = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Código Catálogo SIGA"
    )
    tipo_adquisicion = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('COMPRA', 'Compra'),
            ('DONACION', 'Donación'),
            ('TRANSFERENCIA', 'Transferencia'),
            ('PRODUCCION', 'Producción Propia'),
            ('DREMO', 'dremo'),
        ],
        verbose_name="Tipo de Adquisición"
    )
    numero_documento = models.CharField(max_length=50, blank=True, verbose_name="N° Documento")
    fecha_adquisicion = models.DateField(null=True, blank=True, verbose_name="Fecha de Adquisición")
    valor_inicial = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                        verbose_name="Valor Inicial (S/.)")
    depreciable = models.BooleanField(default=True, verbose_name="¿Es depreciable?")

    # ========== QR ==========
    qr_code = models.ImageField(upload_to='qr/', blank=True, null=True, verbose_name="Código QR")

    # ========== OBSERVACIONES ==========
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")

    # ========== CICLO DE VIDA ==========
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")
    fecha_baja = models.DateField(null=True, blank=True, verbose_name="Fecha de Baja")
    motivo_baja = models.CharField(max_length=200, blank=True, verbose_name="Motivo de Baja")

    class Meta:
        verbose_name = "Bien"
        verbose_name_plural = "Bienes"
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['codigo_patrimonial']),
            models.Index(fields=['sede', 'area']),
            models.Index(fields=['activo']),
            models.Index(fields=['estado_conservacion']),
        ]

    def __str__(self):
        return f"{self.codigo_patrimonial} - {self.denominacion}"

    def generar_qr(self):
        """Genera QR usando la URL del detalle público del bien."""
        if not self.codigo_patrimonial:
            return
        base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
        url = f"{base_url}/bienes/publico/{self.codigo_patrimonial}/"

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        self.qr_code.save(f"qr_{self.codigo_patrimonial}.png", ContentFile(buffer.getvalue()), save=False)

    def save(self, *args, **kwargs):
        if not self.pk or not self.qr_code:
            self.generar_qr()
        super().save(*args, **kwargs)