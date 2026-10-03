from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm

import pandas as pd
from django.db import transaction
from .forms import EstudianteForm, ImportarExcelForm
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
        messages.success(request, "El registro fue eliminado permanentemente.")
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

        messages.success(request, f'¡La información de {estudiante.nombre} se actualizó correctamente!')
        messages.success(request, f'¡La información de {estudiante.nombre} {estudiante.apellido} se actualizó correctamente!')
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
