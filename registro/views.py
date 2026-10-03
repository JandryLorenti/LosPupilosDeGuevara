from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

import pandas as pd
from django.db import transaction
from .forms import EstudianteForm, ImportarExcelForm
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

COLUMNAS_EXCEL = ['cedula', 'nombre', 'apellido', 'correo', 'edad', 'carrera']
MAX_ERRORES_MOSTRADOS = 20


def _lista_con_errores(request, errores):
    # Ahora muestra los errores en la página principal (registrar.html)
    extra = len(errores) - MAX_ERRORES_MOSTRADOS
    return render(request, 'registro/registrar.html', {
        'form': EstudianteForm(),
        'errores_importacion': errores[:MAX_ERRORES_MOSTRADOS],
        'errores_extra': extra if extra > 0 else 0,
    })
    
def importar_excel(request):
    if request.method != 'POST':
        return redirect('registrar')

    form_excel = ImportarExcelForm(request.POST, request.FILES)
    if not form_excel.is_valid():
        errores = [e for lista in form_excel.errors.values() for e in lista]
        return _lista_con_errores(request, errores)

    try:
        df = pd.read_excel(request.FILES['archivo'], dtype=str, keep_default_na=False)
    except Exception:
        return _lista_con_errores(request, ['No se pudo leer el archivo. Verifica que sea un .xlsx válido.'])

    df.columns = [str(c).strip().lower() for c in df.columns]

    faltantes = [c for c in COLUMNAS_EXCEL if c not in df.columns]
    if faltantes:
        return _lista_con_errores(request, ['Faltan columnas en el archivo: ' + ', '.join(faltantes) + '.'])

    df = df[(df[COLUMNAS_EXCEL] != '').any(axis=1)]
    if df.empty:
        return _lista_con_errores(request, ['El archivo no tiene registros.'])

    por_codigo = {codigo.lower(): codigo for codigo, _ in Estudiante.CARRERAS}
    por_nombre = {nombre.lower(): codigo for codigo, nombre in Estudiante.CARRERAS}
    errores = []
    formularios = []
    correos_vistos = {}
    cedulas_vistas = {}

    for indice, fila in df.iterrows():
        n_fila = indice + 2
        datos = {c: str(fila[c]).strip() for c in COLUMNAS_EXCEL}

        clave = datos['carrera'].lower()
        datos['carrera'] = por_codigo.get(clave) or por_nombre.get(clave) or datos['carrera']
        if datos['edad'].endswith('.0'):
            datos['edad'] = datos['edad'][:-2]

        form = EstudianteForm(datos)
        if not form.is_valid():
            for campo, errs in form.errors.items():
                for e in errs:
                    errores.append(f'Fila {n_fila} ({campo}): {e}')
            continue

        correo = form.cleaned_data['correo'].lower()
        cedula = form.cleaned_data['cedula']
        if correo in correos_vistos:
            errores.append(f'Fila {n_fila} (correo): está repetido con la fila {correos_vistos[correo]}.')
        if cedula in cedulas_vistas:
            errores.append(f'Fila {n_fila} (cedula): está repetida con la fila {cedulas_vistas[cedula]}.')
        if Estudiante.objects.filter(cedula=cedula).exists():
            errores.append(f'Fila {n_fila} (cedula): ya existe un estudiante con esa cédula.')
        correos_vistos.setdefault(correo, n_fila)
        cedulas_vistas.setdefault(cedula, n_fila)
        formularios.append(form)

    if errores:
        errores.insert(0, 'Archivo rechazado: no se guardó ningún registro.')
        return _lista_con_errores(request, errores)

    with transaction.atomic():
        for form in formularios:
            form.save()

    messages.success(request, f'Se importaron {len(formularios)} estudiantes correctamente.')
    return redirect('registrar')