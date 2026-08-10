# apps/core/admin.py
from django.contrib import admin
from .models import Sede, Area, Cargo

@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'activo')
    search_fields = ('nombre', 'direccion')
    list_filter = ('activo',)

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sede', 'activo')
    search_fields = ('nombre',)
    list_filter = ('sede', 'activo')

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    search_fields = ('nombre',)
    list_filter = ('activo',)
