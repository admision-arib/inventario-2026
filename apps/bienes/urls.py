# apps/bienes/urls.py
from django.urls import path
from . import views

app_name = 'bienes'

urlpatterns = [
    # Listado (página principal)
    path('', views.lista_bienes, name='lista'),
    # Registro de bien
    path('registro/', views.registro_bien, name='registro'),
    # Detalle público (para QR - sin autenticación)
    path('publico/<str:codigo>/', views.detalle_publico, name='detalle_publico'),
    # Detalle con autenticación
    path('detalle/<str:codigo>/', views.detalle_bien, name='detalle'),
    # Editar bien
    path('editar/<str:codigo>/', views.editar_bien, name='editar'),
    # Dar de baja
    path('baja/<str:codigo>/', views.baja_bien, name='baja'),
    path('importar/', views.importar_bienes, name='importar'),
    path('listar-hojas/', views.listar_hojas, name='listar_hojas'),
    path('area/<int:area_id>/imprimir-qrs/', views.imprimir_qrs_area, name='imprimir_qrs_area'),
    path('asignar-masivo/', views.asignacion_masiva, name='asignar_masivo'),
    path('api/buscar-bienes/', views.buscar_bienes_ajax, name='api_buscar_bienes'),
]

