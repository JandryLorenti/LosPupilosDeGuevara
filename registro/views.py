from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .forms import EstudianteForm
from .models import Estudiante

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

def lista(request):
    estudiantes=Estudiante.objects.order_by('-fecha_registro')
    return render(request, 'registro/lista.html', {'estudiantes': estudiantes})

def eliminar(request, id):
    estudiante = get_object_or_404(Estudiante, id=id)
    if request.method == "POST":
        estudiante.delete()
        messages.success(request, "Registro eliminado.")
    return redirect("lista")
def editar(request, id):
    estudiante = get_object_or_404(Estudiante, id=id)

    if request.method == 'POST':
        nuevo_correo = request.POST.get('correo', '').strip()
        nueva_edad = request.POST.get('edad', '').strip()
        nueva_carrera = request.POST.get('carrera', '').strip()

        # 1. Validar que el correo tenga formato válido
        try:
            validate_email(nuevo_correo)
        except ValidationError:
            messages.error(request, 'El formato del correo no es válido.')
            return render(request, 'registro/editar.html', {'estudiante': estudiante})

        # 2. Validar que el correo no pertenezca ya a otro estudiante (porque correo tiene unique=True)
        if Estudiante.objects.filter(correo=nuevo_correo).exclude(id=estudiante.id).exists():
            messages.error(request, 'Ese correo ya está registrado con otro estudiante.')
            return render(request, 'registro/editar.html', {'estudiante': estudiante})

        # 3. Guardar únicamente los 3 datos permitidos (correo, edad y carrera)
        estudiante.correo = nuevo_correo
        estudiante.edad = int(nueva_edad)
        estudiante.carrera = nueva_carrera
        estudiante.save()

        # 4. Mensaje de confirmación y redirección a la lista
        messages.success(request, f'¡La información de {estudiante.nombre} {estudiante.apellido} se actualizó correctamente!')
        return redirect('lista')

    return render(request, 'registro/editar.html', {'estudiante': estudiante})

def lista(request):
    estudiantes = Estudiante.objects.order_by("-fecha_registro")

    if request.method=="POST":
        buscar = request.POST.get("buscar")
        if buscar:
            estudiantes = estudiantes.filter(nombre__icontains=buscar)

    return render(request,"registro/lista.html",{"estudiantes":estudiantes})

