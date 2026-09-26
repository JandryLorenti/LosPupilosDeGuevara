from django.shortcuts import render, redirect
from django.contrib import messages

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


