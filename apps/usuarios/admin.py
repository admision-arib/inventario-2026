from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'dni', 'email', 'first_name', 'last_name', 'rol', 'cargo', 'area', 'is_active')
    search_fields = ('username', 'dni', 'email', 'first_name', 'last_name')
    list_filter = ('rol', 'is_active', 'cargo', 'area', 'is_staff')

    # Se agregan 'rol' y 'areas_custodia' a la edición en Django Admin
    fieldsets = UserAdmin.fieldsets + (
        ('Información Patrimonial e Institucional', {
            'fields': ('dni', 'rol', 'cargo', 'area', 'areas_custodia', 'telefono')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Patrimonial e Institucional', {
            'fields': ('dni', 'rol', 'cargo', 'area', 'telefono', 'email')
        }),
    )
    filter_horizontal = ('areas_custodia', 'groups', 'user_permissions')

