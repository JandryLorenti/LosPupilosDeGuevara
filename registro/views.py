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

def eliminar(request, id):
    estudiante = get_object_or_404(Estudiante, id=id)
    if request.method == "POST":
        estudiante.delete()
        messages.success(request, "El registro fue eliminado permanentemente.")
    return redirect("lista")

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

        messages.success(request, f'¡La información de {estudiante.nombre} se actualizó correctamente!')
        return redirect('lista')

    return render(request, 'registro/editar.html', {'estudiante': estudiante})

# ÚNICA FUNCIÓN LISTA QUE MANEJA FILTROS, BÚSQUEDA Y ELIMINACIÓN MÚLTIPLE
def lista(request):
    # 1. ELIMINACIÓN MÚLTIPLE (Se captura mediante POST)
    if request.method == "POST" and "eliminar_multiple" in request.POST:
        ids_seleccionados = request.POST.getlist("seleccionados")
        if ids_seleccionados:
            Estudiante.objects.filter(id__in=ids_seleccionados).delete()
            messages.success(request, f"¡Se eliminaron {len(ids_seleccionados)} estudiantes en bloque!")
        else:
            messages.error(request, "No seleccionaste ningún estudiante para eliminar.")
        return redirect("lista")

    # 2. OBTENER TODOS LOS ESTUDIANTES Y APLICAR FILTROS (Vía GET)
    estudiantes = Estudiante.objects.all()

    buscar = request.GET.get("buscar", "")
    carrera = request.GET.get("carrera", "")
    orden = request.GET.get("orden", "-fecha_registro") # -fecha_registro es descendente

    if buscar:
        estudiantes = estudiantes.filter(nombre__icontains=buscar)
    
    if carrera:
        estudiantes = estudiantes.filter(carrera=carrera)

    estudiantes = estudiantes.order_by(orden)

    return render(request, "registro/lista.html", {"estudiantes": estudiantes})