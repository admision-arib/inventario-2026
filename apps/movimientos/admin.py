# apps/movimientos/admin.py
from django.contrib import admin
from .models import MovimientoBien

@admin.register(MovimientoBien)
class MovimientoBienAdmin(admin.ModelAdmin):
    list_display = ('bien', 'tipo', 'fecha_movimiento', 'usuario_origen', 'usuario_destino')
    list_filter = ('tipo', 'fecha_movimiento')
    search_fields = ('bien__codigo_patrimonial',)