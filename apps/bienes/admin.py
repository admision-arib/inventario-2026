from django import forms
from django.contrib import admin, messages
from django.db import transaction
from django.shortcuts import render
from django.utils import timezone

from apps.bienes.models import Bien
from apps.movimientos.models import MovimientoBien
from apps.usuarios.models import Usuario


# 1. FORMULARIO INTERMEDIO DE REASIGNACIÓN
class ReasignarCustodioForm(forms.Form):
  nuevo_custodio = forms.ModelChoiceField(
      queryset=Usuario.objects.filter(is_active=True).order_by(
          'first_name', 'last_name', 'username'
      ),
      required=True,
      label='Seleccionar Nuevo Custodio / Responsable',
      empty_label='-- Seleccione un usuario activo --',
  )


# 2. ACCIÓN MASIVA CON REGISTRO COMPATIBLE CON TU MODELO
@admin.action(description='Reasignar bienes seleccionados a otro Custodio')
def reasignar_custodio_masivo(modeladmin, request, queryset):
  if 'apply' in request.POST:
    form = ReasignarCustodioForm(request.POST)
    if form.is_valid():
      nuevo_custodio = form.cleaned_data['nuevo_custodio']
      ahora = timezone.now()
      reasignados_count = 0

      with transaction.atomic():
        for bien in queryset:
          custodio_anterior = bien.usuario_responsable

          # Registrar el movimiento solo si hay un cambio real de custodio
          if custodio_anterior != nuevo_custodio:
            # A) Crear el registro en el historial de movimientos usando tus campos exactos
            movimiento = MovimientoBien(
                bien=bien,
                tipo='TRANSFERENCIA',
                area_origen=bien.area,
                usuario_origen=custodio_anterior,
                area_destino=bien.area,
                usuario_destino=nuevo_custodio,
                fecha_movimiento=ahora,
                observaciones='Reasignación masiva realizada por el administrador desde el panel de gestión.',
                registrado_por=request.user,
            )
            movimiento.save()  # Llama a full_clean() y guarda de acuerdo a tu modelo

            # B) Actualizar el custodio/responsable en el bien
            bien.usuario_responsable = nuevo_custodio
            bien.save()

            reasignados_count += 1

      modeladmin.message_user(
          request,
          f'Éxito: Se reasignaron {reasignados_count} bienes a'
          f' {nuevo_custodio.get_full_name() or nuevo_custodio.username} y se'
          ' registraron en el historial de traslados.',
          messages.SUCCESS,
      )
      return None

  form = ReasignarCustodioForm()
  return render(
      request,
      'admin/reasignar_custodio_intermediate.html',
      context={
          'bienes': queryset,
          'form': form,
          'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
      },
  )


# 3. REGISTRO EN EL PANEL ADMIN DE BIENES
@admin.register(Bien)
class BienAdmin(admin.ModelAdmin):
  list_display = (
      'codigo_patrimonial',
      'denominacion',
      'area',
      'usuario_responsable',
      'activo',
  )
  list_filter = ('area', 'usuario_responsable', 'activo')
  search_fields = (
      'codigo_patrimonial',
      'denominacion',
      'usuario_responsable__username',
      'usuario_responsable__first_name',
  )
  actions = [reasignar_custodio_masivo]  # <-- AQUÍ SE ENGANCHA LA ACCIÓN