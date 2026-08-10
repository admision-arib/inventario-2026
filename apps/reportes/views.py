import io
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT

from apps.bienes.models import Bien
from apps.core.models import Area
from .models import SesionInventario, DetalleInventario


# ============================
# INICIAR O CARGAR SESIÓN DE INVENTARIO
# ============================
@login_required
@transaction.atomic
def iniciar_o_cargar_inventario(request):
    area_id = request.GET.get('area')
    user = request.user

    # 1. Validar que se haya seleccionado un área
    if not area_id:
        messages.warning(request, "Debe seleccionar un área u oficina para iniciar la verificación física.")
        return redirect('bienes:lista')

    area_obj = get_object_or_404(Area, id=area_id)

    # 2. Identificar al Custodio real a partir de los bienes del Área
    # Buscamos el primer bien activo del área que tenga un usuario_responsable asignado (Ej. Alex)
    primer_bien = Bien.objects.filter(
        area=area_obj,
        activo=True,
        usuario_responsable__isnull=False
    ).select_related('usuario_responsable').first()

    # Si hay bienes con custodio asignado se usa a esa persona, de lo contrario se usa al usuario en sesión
    custodio_real = primer_bien.usuario_responsable if primer_bien else user

    # 3. Buscar si ya existe una sesión en proceso para esa ÁREA
    sesion = SesionInventario.objects.filter(
        area=area_obj,
        estado='EN_PROCESO'
    ).first()

    if not sesion:
        # Se crea la sesión con el Custodio asignado a los bienes y el Verificador actual
        sesion = SesionInventario.objects.create(
            area=area_obj,
            custodio=custodio_real,  # <-- ALEX (Custodio del Área/Bienes)
            realizado_por=user,      # <-- VERIFICADOR / ADMIN (Quien escanea)
            estado='EN_PROCESO'
        )

        # 4. Cargar todos los bienes correspondientes a esa área
        bienes_qs = Bien.objects.filter(area=area_obj, activo=True)

        # Cargar los ítems a verificar de forma masiva
        detalles = [
            DetalleInventario(sesion=sesion, bien=bien) for bien in bienes_qs
        ]
        DetalleInventario.objects.bulk_create(detalles)
    else:
        # Si la sesión ya existía y la retoma otro verificador, actualizamos quién ejecuta el escaneo
        if sesion.realizado_por != user:
            sesion.realizado_por = user
            sesion.save(update_fields=['realizado_por'])

    return redirect('reportes:escaneo_movil', sesion_id=sesion.id)


# ============================
# ESCANEO MÓVIL
# ============================
@login_required
def escaneo_movil(request, sesion_id):
    """
    Interfaz adaptada para dispositivos móviles / cámara QR.
    """
    sesion = get_object_or_404(SesionInventario, id=sesion_id)

    # Control de acceso a la sesión
    if not request.user.es_inventariador_o_admin and sesion.custodio != request.user:
        messages.error(request, "❌ No tiene permisos para acceder a esta sesión de inventario.")
        return redirect('bienes:lista')

    detalles = sesion.detalles.select_related('bien').order_by('-verificado', 'bien__codigo_patrimonial')

    total = detalles.count()
    escaneados = detalles.filter(verificado=True).count()
    progreso = int((escaneados / total * 100)) if total > 0 else 0

    return render(request, 'reportes/escaneo_movil.html', {
        'sesion': sesion,
        'detalles': detalles,
        'total': total,
        'escaneados': escaneados,
        'progreso': progreso
    })


# ============================
# VERIFICACIÓN DE CÓDIGO QR (API AJAX)
# ============================
@login_required
def verificar_codigo_qr(request, sesion_id):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()

        # 1. Limpieza de saltos de línea (por si el QR trae texto multilínea)
        codigo = codigo.split('\n')[0].split('\r')[0].strip()

        # 2. Parche para URLs (si el QR contiene una URL como http://localhost:8000/.../BN-ALMAC-2026-00043/)
        if 'http' in codigo.lower():
            partes = [p for p in codigo.split('/') if p.strip()]
            if partes:
                codigo = partes[-1]

        sesion = get_object_or_404(SesionInventario, id=sesion_id)

        detalle = sesion.detalles.filter(
            Q(bien__codigo_patrimonial__iexact=codigo) | Q(bien__serie__iexact=codigo)
        ).first()

        if detalle:
            detalle.verificado = True
            detalle.estado_hallazgo = 'VERIFICADO'
            detalle.fecha_escaneo = timezone.now()
            detalle.save()

            return JsonResponse({
                'status': 'ok',
                'mensaje': f' {detalle.bien.denominacion} verificado con éxito.',
                'bien_id': detalle.bien.id
            })
        else:
            return JsonResponse({
                'status': 'error',
                'mensaje': ' El código escaneado no corresponde a los bienes asignados a esta sesión.'
            }, status=400)

    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)


# ============================
# ACTA DE CONSOLIDACIÓN Y VERIFICACIÓN EN PDF
# ============================
@login_required
def generar_acta_consolidacion_pdf(request):
  sesion_id = request.GET.get('sesion_id')
  if not sesion_id:
    return HttpResponse('No se proporcionó un ID de sesión válido.', status=400)

  sesion = get_object_or_404(SesionInventario, id=sesion_id)

  # Finalizar la sesión al generar el acta oficial
  if sesion.estado != 'FINALIZADO':
    sesion.estado = 'FINALIZADO'
    sesion.fecha_cierre = timezone.now()
    sesion.save()

  detalles = sesion.detalles.select_related('bien', 'bien__area').order_by(
      'bien__codigo_patrimonial'
  )

  # Datos para el encabezado
  area_nombre = (
      sesion.area.nombre.upper() if sesion.area else 'ÁREA NO ESPECIFICADA'
  )

  # 1. EXTRACCIÓN DINÁMICA DE DATOS PARA LAS FIRMAS (Nombre y DNI)
  # Custodio
  c_user = sesion.custodio
  custodio_nombre = (
      c_user.get_full_name().upper()
      if c_user and c_user.get_full_name().strip()
      else (c_user.username.upper() if c_user else 'SIN ASIGNAR')
  )
  custodio_dni = (
      getattr(c_user, 'dni', None)
      or getattr(c_user, 'username', '—')
      if c_user
      else '—'
  )

  # Responsable de Patrimonio / Verificador
  v_user = sesion.realizado_por
  verificador_nombre = (
      v_user.get_full_name().upper()
      if v_user and v_user.get_full_name().strip()
      else (v_user.username.upper() if v_user else 'SIN ASIGNAR')
  )
  verificador_dni = (
      getattr(v_user, 'dni', None)
      or getattr(v_user, 'username', '—')
      if v_user
      else '—'
  )

  # Configuración del PDF con ReportLab
  buffer = io.BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=letter,
      rightMargin=36,
      leftMargin=36,
      topMargin=36,
      bottomMargin=36,
  )
  story = []
  styles = getSampleStyleSheet()

  # Estilos
  titulo_style = ParagraphStyle(
      'T1',
      parent=styles['Normal'],
      fontName='Helvetica-Bold',
      fontSize=12,
      leading=15,
      alignment=TA_CENTER,
      textColor=colors.HexColor('#1E293B'),
  )
  subtitulo_style = ParagraphStyle(
      'T2',
      parent=styles['Normal'],
      fontName='Helvetica',
      fontSize=8.5,
      leading=11,
      alignment=TA_CENTER,
      textColor=colors.HexColor('#64748B'),
  )
  body_bold = ParagraphStyle(
      'B1',
      parent=styles['Normal'],
      fontName='Helvetica-Bold',
      fontSize=8,
      leading=10,
      textColor=colors.HexColor('#1E293B'),
  )
  body_normal = ParagraphStyle(
      'B2',
      parent=styles['Normal'],
      fontName='Helvetica',
      fontSize=8,
      leading=10,
      textColor=colors.HexColor('#334155'),
  )
  cell_style = ParagraphStyle(
      'C1',
      parent=styles['Normal'],
      fontName='Helvetica',
      fontSize=7,
      leading=9,
      textColor=colors.HexColor('#1E293B'),
  )
  cell_header = ParagraphStyle(
      'CH',
      parent=styles['Normal'],
      fontName='Helvetica-Bold',
      fontSize=7,
      leading=9,
      alignment=TA_CENTER,
      textColor=colors.HexColor('#FFFFFF'),
  )

  # Encabezado Institucional
  story.append(
      Paragraph('IESTP ALIANZA RENOVADA ICHUÑA BÉLGICA', titulo_style)
  )
  story.append(Spacer(1, 2))
  story.append(
      Paragraph(
          'ACTA DE CONSOLIDACIÓN Y VERIFICACIÓN FÍSICA DE BIENES',
          titulo_style,
      )
  )
  story.append(Spacer(1, 3))
  fecha_cierre_str = (
      sesion.fecha_cierre.strftime('%d/%m/%Y %H:%M')
      if sesion.fecha_cierre
      else timezone.now().strftime('%d/%m/%Y %H:%M')
  )
  story.append(
      Paragraph(
          f'N° Control Inventario: AUD-{sesion.id:05d} | Fecha Cierre:'
          f' {fecha_cierre_str}',
          subtitulo_style,
      )
  )
  story.append(Spacer(1, 8))
  story.append(
      HRFlowable(
          width='100%',
          thickness=1,
          color=colors.HexColor('#CBD5E1'),
          spaceAfter=8,
      )
  )

  # Metadatos
  info_data = [
      [
          Paragraph('<b>RESPONSABLE/CUSTODIO:</b>', body_bold),
          Paragraph(custodio_nombre, body_normal),
          Paragraph('<b>TOTAL REVISADOS:</b>', body_bold),
          Paragraph(
              f'{detalles.filter(verificado=True).count()} de'
              f' {detalles.count()}',
              body_bold,
          ),
      ],
      [
          Paragraph('<b>ÁREA / OFICINA:</b>', body_bold),
          Paragraph(area_nombre, body_normal),
          Paragraph('<b>VERIFICACIÓN QR:</b>', body_bold),
          Paragraph('CONFORME EN CAMPO', body_bold),
      ],
  ]

  t_info = Table(info_data, colWidths=[120, 220, 90, 110])
  t_info.setStyle(
      TableStyle([
          ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
          ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
          ('TOPPADDING', (0, 0), (-1, -1), 2),
      ])
  )
  story.append(t_info)
  story.append(Spacer(1, 10))

  # Tabla de Resultados
  table_data = [[
      Paragraph('<b>N°</b>', cell_header),
      Paragraph('<b>CÓDIGO PATR.</b>', cell_header),
      Paragraph('<b>DENOMINACIÓN / DESCRIPCIÓN</b>', cell_header),
      Paragraph('<b>MARCA / SERIE</b>', cell_header),
      Paragraph('<b>VERIFICACIÓN FÍSICA</b>', cell_header),
  ]]

  for idx, item in enumerate(detalles, start=1):
    bien = item.bien
    detalles_marca = f"{bien.marca or ''} {bien.modelo or ''}".strip()
    if bien.serie:
      detalles_marca += f' / S/N: {bien.serie}'

    estado_check = 'VERIFICADO (QR)' if item.verificado else 'NO LOCALIZADO'
    color_check = (
        colors.HexColor('#166534')
        if item.verificado
        else colors.HexColor('#991B1B')
    )

    row = [
        Paragraph(
            str(idx), ParagraphStyle('Cen', parent=cell_style, alignment=TA_CENTER)
        ),
        Paragraph(
            bien.codigo_patrimonial,
            ParagraphStyle('Cod', parent=cell_style, fontName='Helvetica-Bold'),
        ),
        Paragraph(bien.denominacion, cell_style),
        Paragraph(detalles_marca or '—', cell_style),
        Paragraph(
            f'<b>{estado_check}</b>',
            ParagraphStyle(
                'Chk',
                parent=cell_style,
                alignment=TA_CENTER,
                textColor=color_check,
            ),
        ),
    ]
    table_data.append(row)

  t_bienes = Table(table_data, colWidths=[25, 95, 200, 120, 100], repeatRows=1)
  t_bienes.setStyle(
      TableStyle([
          ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
          ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
          ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
          ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
          ('TOPPADDING', (0, 0), (-1, -1), 3),
          ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
          (
              'ROWBACKGROUNDS',
              (0, 1),
              (-1, -1),
              [colors.white, colors.HexColor('#F8FAFC')],
          ),
      ])
  )

  story.append(t_bienes)
  story.append(Spacer(1, 15))

  # Firmas y Declaración
  texto_compromiso = (
      'El custodio y el responsable de inventario certifican que se realizó la'
      ' verificación física por escaneo de código QR de los activos detallados.'
      ' Se asume la responsabilidad administrativa de su correcto uso y'
      ' conservación.'
  )
  story.append(
      Paragraph(
          texto_compromiso,
          ParagraphStyle('Comp', parent=body_normal, alignment=TA_JUSTIFY),
      )
  )
  story.append(Spacer(1, 40))

  # 2. BLOQUE DE FIRMAS CON NOMBRES Y DNI AUTOMÁTICOS
  firmas_data = [[
      Paragraph(
          f'___________________________________<br/>'
          f'<b>{custodio_nombre}</b><br/>'
          f'DNI: {custodio_dni}<br/>'
          f'<b>CUSTODIO DE LOS BIENES</b><br/>'
          f'IESTP ARIB',
          ParagraphStyle('F1', parent=body_normal, alignment=TA_CENTER),
      ),
      Paragraph(
          f'___________________________________<br/>'
          f'<b>{verificador_nombre}</b><br/>'
          f'DNI: {verificador_dni}<br/>'
          f'<b>RESPONSABLE DE PATRIMONIO</b><br/>'
          f'IESTP ARIB',
          ParagraphStyle('F2', parent=body_normal, alignment=TA_CENTER),
      ),
  ]]
  t_firmas = Table(firmas_data, colWidths=[270, 270])
  story.append(t_firmas)

  # Generar PDF
  doc.build(story)
  buffer.seek(0)

  filename = f'Acta_Verificacion_QR_{sesion.id}.pdf'
  response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
  response['Content-Disposition'] = f'inline; filename="{filename}"'
  return response