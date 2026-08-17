from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('inventario/iniciar/', views.iniciar_o_cargar_inventario, name='iniciar_inventario'),
    path('inventario/<int:sesion_id>/escaneo/', views.escaneo_movil, name='escaneo_movil'),
    path('inventario/<int:sesion_id>/verificar/', views.verificar_codigo_qr, name='verificar_codigo_qr'),
    #path('inventario/<int:sesion_id>/acta-pdf/', views.generar_acta_consolidacion_pdf, name='generar_acta_pdf'),  # <-- AGREGAR ESTA LÍNEA
    path('acta-consolidacion/pdf/', views.generar_acta_consolidacion_pdf, name='acta_consolidacion_pdf'),
    path('inventario-general/pdf/', views.generar_inventario_general_pdf, name='inventario_general_pdf'),
    path('informe-dremo/pdf/', views.generar_informe_dremo_pdf, name='informe_dremo_pdf'),

]