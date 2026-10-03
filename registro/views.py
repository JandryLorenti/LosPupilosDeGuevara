from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm

from .forms import EstudianteForm
from .models import Estudiante

# Regla de seguridad: Solo pasan los superusuarios
def es_admin(user):
    return user.is_superuser

@login_required
def registrar(request):
    if request.method=='POST':
        form=EstudianteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Registro guardado con éxito!')
            return redirect('registrar')
    else: 
        form=EstudianteForm()
    return render(request, 'registro/registrar.html', {'form': form})

@login_required
def lista(request):
    # Función unificada: carga la lista y hace la búsqueda si es POST
    estudiantes = Estudiante.objects.order_by("-fecha_registro")

    if request.method == "POST":
        buscar = request.POST.get("buscar")
        if buscar:
            estudiantes = estudiantes.filter(nombre__icontains=buscar)

    return render(request, "registro/lista.html", {"estudiantes": estudiantes})

@login_required
def eliminar(request, id):
    estudiante = get_object_or_404(Estudiante, id=id)
    if request.method == "POST":
        estudiante.delete()
        messages.success(request, "Registro eliminado.")
    return redirect("lista")

@login_required
def editar(request, id):
    estudiante = get_object_or_404(Estudiante, id=id)

    if request.method == 'POST':
        nuevo_correo = request.POST.get('correo', '').strip()
        nueva_edad = request.POST.get('edad', '').strip()
        nueva_carrera = request.POST.get('carrera', '').strip()

        try:
            validate_email(nuevo_correo)
        except ValidationError:
            messages.error(request, 'El formato del correo no es válido.')
            return render(request, 'registro/editar.html', {'estudiante': estudiante})

        if Estudiante.objects.filter(correo=nuevo_correo).exclude(id=estudiante.id).exists():
            messages.error(request, 'Ese correo ya está registrado con otro estudiante.')
            return render(request, 'registro/editar.html', {'estudiante': estudiante})

        estudiante.correo = nuevo_correo
        estudiante.edad = int(nueva_edad)
        estudiante.carrera = nueva_carrera
        estudiante.save()

        messages.success(request, f'¡La información de {estudiante.nombre} {estudiante.apellido} se actualizó correctamente!')
        return redirect('lista')

    return render(request, 'registro/editar.html', {'estudiante': estudiante})

# Candado especial para crear cuentas (Solo Superusuarios)
@user_passes_test(es_admin, login_url='registrar')
def registro_usuario(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Usuario creado con éxito! Ya puedes entregarle sus credenciales.')
            return redirect('registrar') 
    else:
        form = UserCreationForm()
        
    return render(request, 'registration/registro_usuario.html', {'form': form})    