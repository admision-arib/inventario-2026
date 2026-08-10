from django.contrib import admin
from .models import SesionInventario, DetalleInventario


class DetalleInventarioInline(admin.TabularInline):
    model = DetalleInventario
    extra = 0
    readonly_fields = ('bien', 'verificado', 'estado_hallazgo', 'fecha_escaneo')
    can_delete = False


@admin.register(SesionInventario)
class SesionInventarioAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'area',
        'mostrar_custodio',
        'mostrar_realizado_por',
        'estado',
        'fecha_inicio',
        'fecha_cierre'
    )

    def mostrar_custodio(self, obj):
        if obj.custodio:
            nombre_completo = obj.custodio.get_full_name().strip()
            # Si tiene nombre/apellido muestra el nombre completo, sino el username (ej. 'admin')
            return nombre_completo if nombre_completo else f"{obj.custodio.username} ({obj.custodio.id})"
        return "-"
    mostrar_custodio.short_description = 'Custodio'

    def mostrar_realizado_por(self, obj):
        if obj.realizado_por:
            nombre_completo = obj.realizado_por.get_full_name().strip()
            return nombre_completo if nombre_completo else f"{obj.realizado_por.username} ({obj.realizado_por.id})"
        return "-"
    mostrar_realizado_por.short_description = 'Realizado por'