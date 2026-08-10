# apps/usuarios/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import ModeloAuditable, Cargo, Area


class Usuario(AbstractUser, ModeloAuditable):
    """
    Modelo de usuario personalizado para el IESTP ARIB.
    """

    class Roles(models.TextChoices):
        ADMINISTRADOR = 'ADMIN', 'Administrador Patrimonial'
        INVENTARIADOR = 'INVENTARIADOR', 'Inventariador / Verificador'
        CUSTODIO = 'CUSTODIO', 'Custodio / Personal'

    dni = models.CharField(max_length=8, unique=True, verbose_name="DNI")

    email = models.EmailField(
        unique=True,
        blank=False,
        null=False,
        verbose_name="Correo electrónico"
    )
    cargo = models.ForeignKey(
        Cargo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Cargo"
    )

    # Área de adscripción principal (Oficina física donde labora o está asignado administrativamente)
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios_principales",
        verbose_name="Área Principal"
    )

    # ÁREAS A SU CARGO / EN CUSTODIA (1 o varias áreas, como Biblioteca + Almacén)
    areas_custodia = models.ManyToManyField(
        Area,
        blank=True,
        related_name="custodios_responsables",
        verbose_name="Áreas en Custodia / A Su Cargo"
    )

    rol = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CUSTODIO,
        verbose_name="Rol en el Sistema"
    )

    telefono = models.CharField(max_length=15, blank=True, verbose_name="Teléfono")

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.dni})"

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.dni
        super().save(*args, **kwargs)

    @property
    def es_inventariador_o_admin(self):
        """Devuelve True si es Administrador o Verificador/Inventariador de campo."""
        return self.rol in [self.Roles.ADMINISTRADOR, self.Roles.INVENTARIADOR] or self.is_superuser or self.is_staff

    @property
    def es_custodio_puro(self):
        """Devuelve True si su perfil es únicamente Custodio/Personal."""
        return self.rol == self.Roles.CUSTODIO and not (self.is_superuser or self.is_staff)