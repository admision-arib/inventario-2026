# apps/usuarios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from .models import Usuario
from .forms import UsuarioForm


def es_administrador(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser or getattr(user, 'rol', '') == 'ADMIN')


@login_required
@user_passes_test(es_administrador)
def lista_usuarios(request):
    # Optimizamos la consulta trayendo el cargo, área principal y áreas bajo custodia
    usuarios = Usuario.objects.all().select_related(
        'cargo', 'area'
    ).prefetch_related(
        'areas_custodia'
    ).order_by('-date_joined')

    paginator = Paginator(usuarios, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'usuarios/lista.html', {'page_obj': page_obj})


@login_required
@user_passes_test(es_administrador)
def crear_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(
                request,
                f"✅ Usuario {usuario.get_full_name()} creado exitosamente. (Contraseña: {usuario.dni if not request.POST.get('password') else 'personalizada'})"
            )
            return redirect('usuarios:lista')
        else:
            messages.error(request, " Revise los campos del formulario.")
    else:
        form = UsuarioForm()

    return render(request, 'usuarios/form.html', {'form': form, 'titulo': 'Crear Usuario'})


@login_required
@user_passes_test(es_administrador)
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f" Usuario {usuario.get_full_name()} actualizado.")
            return redirect('usuarios:lista')
        else:
            messages.error(request, " Revise los campos del formulario.")
    else:
        form = UsuarioForm(instance=usuario)

    return render(request, 'usuarios/form.html', {'form': form, 'titulo': 'Editar Usuario', 'usuario': usuario})


@login_required
@user_passes_test(es_administrador)
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        if usuario.pk == request.user.pk:
            messages.error(request, " No puedes eliminarte a ti mismo.")
            return redirect('usuarios:lista')

        nombre = usuario.get_full_name()
        usuario.delete()
        messages.warning(request, f" Usuario {nombre} eliminado.")
        return redirect('usuarios:lista')

    return render(request, 'usuarios/confirmar_eliminar.html', {'usuario': usuario})