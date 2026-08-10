# apps/usuarios/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'usuarios'

urlpatterns = [
# ========== AUTENTICACIÓN (LOGIN / LOGOUT) ==========
    path('login/', auth_views.LoginView.as_view(
        template_name='usuarios/login.html',
        redirect_authenticated_user=True
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='usuarios:login'
    ), name='logout'),
    path('', views.lista_usuarios, name='lista'),
    path('crear/', views.crear_usuario, name='crear'),
    path('editar/<int:pk>/', views.editar_usuario, name='editar'),
    path('eliminar/<int:pk>/', views.eliminar_usuario, name='eliminar'),
]