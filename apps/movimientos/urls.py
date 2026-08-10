from django.urls import path
from . import views

app_name = 'movimientos'

urlpatterns = [
    # Historial de movimientos
    path('', views.historial_movimientos, name='historial'),

    # Transferencia general
    path('transferir/', views.registrar_transferencia, name='registrar_transferencia'),

    # Transferencia directa de un bien específico
    path('transferir/<str:codigo_bien>/', views.registrar_transferencia, name='transferir_bien'),

    # Detalle de un movimiento
    path('<int:pk>/', views.detalle_movimiento, name='detalle'),

    # Vista para imprimir Acta/Papeleta de desplazamiento
    path('<int:pk>/acta/', views.acta_movimiento, name='acta'),
]