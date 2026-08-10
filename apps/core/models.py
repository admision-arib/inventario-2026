# apps/core/models.py
from django.db import models
from django.conf import settings

class ModeloAuditable(models.Model):
    """
    Clase abstracta que añade campos de auditoría a cualquier modelo.
    Satisfacción del Driver QA-1 (Auditoría Transversal).
    - creado_por: Usuario que creó el registro.
    - modificado_por: Usuario que modificó por última vez.
    - creado_en / modificado_en: Fechas automáticas.
    """
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # No bloquear eliminación de usuarios (política realista)
        null=True,
        blank=True,
        related_name="%(class)s_creados",
        verbose_name="Creado por"
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_modificados",
        verbose_name="Modificado por"
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    modificado_en = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Si es nuevo y no tiene creado_por, se asigna automáticamente en la señal.
        # Pero dejamos la lógica en la señal para mantener separación de responsabilidades.
        super().save(*args, **kwargs)


class Sede(ModeloAuditable):
    """Representa una sede física del IESTP ARIB."""
    nombre = models.CharField(max_length=150, unique=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Sede"
        verbose_name_plural = "Sedes"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Area(ModeloAuditable):
    """Área u oficina dentro de una sede. Ej: Biblioteca, Taller Mecánico, etc."""
    nombre = models.CharField(max_length=150)
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name="areas")
    custodio = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='areas_a_cargo',
        verbose_name='Custodio / Responsable',
    )
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('nombre', 'sede')
        verbose_name = "Área"
        verbose_name_plural = "Áreas"
        ordering = ['sede__nombre', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.sede.nombre})"


class Cargo(ModeloAuditable):
    """
    Representa el cargo o puesto que ocupa un usuario dentro de la institución.
    Ejemplos: Secretario Académico, Bibliotecario, Coordinador de Minas, etc.
    No incluye jerarquía numérica porque la jerarquía se define por la estructura orgánica.
    """
    nombre = models.CharField(max_length=150, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

