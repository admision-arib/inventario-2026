from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import MovimientoBien
from .forms import TransferenciaForm
from apps.bienes.models import Bien


# ============================
# HISTORIAL DE MOVIMIENTOS
# ============================
@login_required
def historial_movimientos(request):
    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()

    movimientos_qs = MovimientoBien.objects.select_related(
        'bien', 'area_origen', 'usuario_origen', 'area_destino', 'usuario_destino', 'registrado_por'
    ).all()

    if not request.user.es_inventariador_o_admin:
        mis_areas_ids = request.user.areas_custodia.values_list('id', flat=True)
        movimientos_qs = movimientos_qs.filter(
            Q(usuario_origen=request.user) |
            Q(usuario_destino=request.user) |
            Q(area_origen_id__in=mis_areas_ids) |
            Q(area_destino_id__in=mis_areas_ids)
        ).distinct()

    if tipo:
        movimientos_qs = movimientos_qs.filter(tipo=tipo)

    if query:
        movimientos_qs = movimientos_qs.filter(
            Q(bien__codigo_patrimonial__icontains=query) |
            Q(bien__denominacion__icontains=query) |
            Q(documento_autorizacion__icontains=query)
        )

    paginator = Paginator(movimientos_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'tipo_seleccionado': tipo,
        'tipos_choices': MovimientoBien.TIPO_CHOICES,
    }
    return render(request, 'movimientos/historial.html', context)


# ============================
# REGISTRAR TRANSFERENCIA
# ============================
@login_required
def registrar_transferencia(request, codigo_bien=None):
    if not request.user.es_inventariador_o_admin:
        messages.error(request, " No tiene permisos para registrar transferencias de bienes.")
        return redirect('movimientos:historial')

    bien_inicial = None
    if codigo_bien:
        bien_inicial = get_object_or_404(Bien, codigo_patrimonial=codigo_bien, activo=True)

    if request.method == 'POST':
        form = TransferenciaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    movimiento = form.save(commit=False)
                    bien = movimiento.bien

                    # Cargar datos de origen directamente del bien
                    movimiento.area_origen = bien.area
                    movimiento.usuario_origen = bien.usuario_responsable
                    movimiento.tipo = 'TRANSFERENCIA'
                    movimiento.fecha_movimiento = timezone.now()
                    movimiento.registrado_por = request.user

                    # Ejecutar validaciones del modelo antes de guardar
                    movimiento.full_clean()
                    movimiento.save()

                    # Actualizar la ubicación y responsabilidad del bien
                    bien.area = movimiento.area_destino
                    bien.sede = movimiento.area_destino.sede
                    bien.usuario_responsable = movimiento.usuario_destino
                    bien.save(update_fields=['area', 'sede', 'usuario_responsable'])

                    messages.success(
                        request,
                        f" Bien {bien.codigo_patrimonial} transferido exitosamente a "
                        f"{movimiento.usuario_destino.get_full_name()} ({movimiento.area_destino.nombre})."
                    )
                    return redirect('movimientos:detalle', pk=movimiento.pk)

            except ValidationError as e:
                # Se capturan los errores de validación del modelo/limpieza y se muestran al usuario
                if hasattr(e, 'message_dict'):
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            messages.error(request, f" {error}")
                else:
                    for error in e.messages:
                        messages.error(request, f" {error}")
            except Exception as e:
                messages.error(request, f" Ocurrió un error inesperado al procesar la transferencia: {str(e)}")
        else:
            messages.error(request, " Por favor revise los datos ingresados en el formulario.")
    else:
        initial_data = {}
        if bien_inicial:
            initial_data['bien'] = bien_inicial
        form = TransferenciaForm(initial=initial_data)

    return render(request, 'movimientos/registrar_transferencia.html', {
        'form': form,
        'bien_inicial': bien_inicial
    })


# ============================
# DETALLE DEL MOVIMIENTO
# ============================
@login_required
def detalle_movimiento(request, pk):
    movimiento = get_object_or_404(
        MovimientoBien.objects.select_related(
            'bien', 'area_origen', 'usuario_origen', 'area_destino', 'usuario_destino', 'registrado_por'
        ),
        pk=pk
    )
    return render(request, 'movimientos/detalle.html', {'movimiento': movimiento})


# ============================
# ACTA DE TRANSFERENCIA (IMPRESIÓN / CARGO)
# ============================
@login_required
def acta_movimiento(request, pk):
    movimiento = get_object_or_404(
        MovimientoBien.objects.select_related(
            'bien', 'area_origen', 'usuario_origen', 'area_destino', 'usuario_destino', 'registrado_por'
        ),
        pk=pk
    )
    return render(request, 'movimientos/acta_pdf.html', {'movimiento': movimiento})