from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from .models import UserForm, Enfermero, Paciente, Medicamento, Pastillero, HorarioPastillero
from .forms import EnfermeroForm, PacienteForm, MedicamentoForm, HorarioPastilleroForm
from pymongo import MongoClient
from bson import ObjectId
from mongoengine.errors import DoesNotExist, ValidationError
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime

"""
from .models import Paciente, Medicamento, Pastillero
from .forms import PacienteForm, MedicamentoForm, HorarioForm, PastilleroForm
"""


client = MongoClient("mongodb+srv://regina:pKW6Ir1kXLapHf5u@pillstation.c4ue9.mongodb.net/?retryWrites=true&w=majority&appName=PillStation")
db = client["PillStation"]

def index(request):
    return render(request, 'index.html')

def register(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = make_password(form.cleaned_data['password'])
            if db.users.find_one({'email': email}):
                return render(request, 'register.html', {'form': form, 'error': 'Email already exists'})
            db.users.insert_one({'username': username, 'email': email, 'password': password})
            return redirect('login')
    else:
        form = UserForm()
    return render(request, 'register.html', {'form': form})

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = db.users.find_one({'username': username})
        if user and check_password(password, user['password']): 
            request.session['username'] = username
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')

def home(request):
    if 'username' not in request.session:
        return redirect('home.html')
    username = request.session['username']
    return render(request, 'home.html', {'username': username})


def userHome(request):
    return render(request, 'home.html')


def logout(request):
    request.session.flush()
    return redirect('login')

#ailton esp32

from django.http import JsonResponse
def esp32_endpoint(request):
    data = {
        "message": "Hola Esp32, Django esta funcionando correctamente "

    }
    return JsonResponse(data)

"""
def agregar_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_pacientes')
    else:
        form = PacienteForm()
    return render(request, 'agregar_paciente.html', {'form': form})

def editar_paciente(request, id):
    paciente = get_object_or_404(Paciente, id=id)
    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            return redirect('lista_pacientes')
    else:
        form = PacienteForm(instance=paciente)
    return render(request, 'editar_paciente.html', {'form': form})

def eliminar_paciente(request, id):
    paciente = get_object_or_404(Paciente, id=id)
    paciente.delete()
    return redirect('lista_pacientes')


# Listar medicamentos
def lista_medicamentos(request):
    medicamentos = Medicamento.objects.all()
    return render(request, 'lista_medicamentos.html', {'medicamentos': medicamentos})

# Agregar medicamento
def agregar_medicamento(request):
    if request.method == 'POST':
        form = MedicamentoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_medicamentos')
    else:
        form = MedicamentoForm()
    return render(request, 'agregar_medicamento.html', {'form': form})

# Editar medicamento
def editar_medicamento(request, id):
    medicamento = get_object_or_404(Medicamento, id=id)
    if request.method == 'POST':
        form = MedicamentoForm(request.POST, instance=medicamento)
        if form.is_valid():
            form.save()
            return redirect('lista_medicamentos')
    else:
        form = MedicamentoForm(instance=medicamento)
    return render(request, 'editar_medicamento.html', {'form': form})

# Eliminar medicamento
def eliminar_medicamento(request, id):
    medicamento = get_object_or_404(Medicamento, id=id)
    medicamento.delete()
    return redirect('lista_medicamentos')

# Listar horarios
def lista_horarios(request):
    horarios = Horario.objects.all()
    return render(request, 'lista_horarios.html', {'horarios': horarios})

# Agregar horario
def agregar_horario(request):
    if request.method == 'POST':
        form = HorarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_horarios')
    else:
        form = HorarioForm()
    return render(request, 'agregar_horario.html', {'form': form})

# Editar horario
def editar_horario(request, id):
    horario = get_object_or_404(Horario, id=id)
    if request.method == 'POST':
        form = HorarioForm(request.POST, instance=horario)
        if form.is_valid():
            form.save()
            return redirect('lista_horarios')
    else:
        form = HorarioForm(instance=horario)
    return render(request, 'editar_horario.html', {'form': form})

# Eliminar horario
def eliminar_horario(request, id):
    horario = get_object_or_404(Horario, id=id)
    horario.delete()
    return redirect('lista_horarios')

# Listar pastilleros
def lista_pastilleros(request):
    pastilleros = Pastillero.objects.all()
    return render(request, 'lista_pastilleros.html', {'pastilleros': pastilleros})

# Agregar pastillero
def agregar_pastillero(request):
    if request.method == 'POST':
        form = PastilleroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_pastilleros')
    else:
        form = PastilleroForm()
    return render(request, 'agregar_pastillero.html', {'form': form})

# Editar pastillero
def editar_pastillero(request, id):
    pastillero = get_object_or_404(Pastillero, id=id)
    if request.method == 'POST':
        form = PastilleroForm(request.POST, instance=pastillero)
        if form.is_valid():
            form.save()
            return redirect('lista_pastilleros')
    else:
        form = PastilleroForm(instance=pastillero)
    return render(request, 'editar_pastillero.html', {'form': form})

# Eliminar pastillero
def eliminar_pastillero(request, id):
    pastillero = get_object_or_404(Pastillero, id=id)
    pastillero.delete()
    return redirect('lista_pastilleros')

# Vista para generar reportes de medicamentos
def generar_reporte(request):
    if request.method == 'POST':
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        reporte = Medicamento.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
        return render(request, 'reporte.html', {'reporte': reporte})
    return render(request, 'generar_reporte.html')

"""

# E N F E R M E R O S

# Crear un nuevo enfermero
def crear_enfermero(request):
    if request.method == 'POST':
        form = EnfermeroForm(request.POST)
        if form.is_valid():
            nuevo_enfermero = Enfermero(
                nombre=form.cleaned_data['nombre'],
                apellidos=form.cleaned_data['apellidos'],
                nfc_id=form.cleaned_data['nfc_id'],
                turno=form.cleaned_data['turno'],
                activo=form.cleaned_data['activo'],
                usuario=form.cleaned_data['usuario'],
                password=form.cleaned_data['password'],
                email=form.cleaned_data['email'],
                TelefonoCel=form.cleaned_data['TelefonoCel']
            )
            nuevo_enfermero.save()
            return redirect('enfermero_list')  
    else:
        form = EnfermeroForm() 

    return render(request, 'nurse/create.html', {'form': form})

# Editar un enfermero existente
def editar_enfermero(request, pk):
    try:
        enfermero = Enfermero.objects.get(pk=pk)
    except DoesNotExist:
        return redirect('enfermero_list')

    if request.method == 'POST':
        form = EnfermeroForm(request.POST, instance=enfermero)
        if form.is_valid():
            enfermero.nombre = form.cleaned_data['nombre']
            enfermero.apellidos = form.cleaned_data['apellidos']
            enfermero.nfc_id = form.cleaned_data['nfc_id']
            enfermero.turno = form.cleaned_data['turno']
            enfermero.activo = form.cleaned_data['activo']
            enfermero.usuario = form.cleaned_data['usuario']
            enfermero.password = form.cleaned_data['password']
            enfermero.email = form.cleaned_data['email']
            enfermero.TelefonoCel = form.cleaned_data['TelefonoCel']
            enfermero.save()

            return redirect('enfermero_list') 
    else:
        form = EnfermeroForm(instance=enfermero)  

    return render(request, 'nurse/edit.html', {'form': form, 'enfermero': enfermero})

# Listar todos los enfermeros
def listar_enfermeros(request):
    enfermeros = Enfermero.objects.all()
    for enfermero in enfermeros:
        print(enfermero.pk)
    return render(request, 'nurse/list.html', {'enfermeros': enfermeros})

# Eliminar un enfermero
def eliminar_enfermero(request, pk):
    try:
        enfermero = Enfermero.objects.get(id=pk)
    except Enfermero.DoesNotExist:
        return redirect('enfermero_list')

    if request.method == 'POST':
        enfermero.delete()
        return redirect('enfermero_list')

    return render(request, 'nurse/delete.html', {'enfermero': enfermero})

# P A C I E N T E S 

# Crear un nuevo paciente
def crear_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            paciente = Paciente(
                fecha_ingreso=form.cleaned_data['fecha_ingreso'],
                fecha_de_salida=form.cleaned_data.get('fecha_de_salida')
            )
            paciente.save() 
            return redirect('paciente_list') 
    else:
        form = PacienteForm()

    return render(request, 'patient/create.html', {'form': form})

# Listar todos los pacientes
def listar_pacientes(request):
    pacientes = Paciente.objects.all() 
    return render(request, 'patient/list.html', {'pacientes': pacientes})

# Editar un paciente existente
def editar_paciente(request, pk):
    try:
        paciente = Paciente.objects.get(pk=pk)
    except DoesNotExist:
        return redirect('listar_pacientes')
    
    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            paciente.fecha_ingreso = form.cleaned_data['fecha_ingreso']
            if 'fecha_salida' in form.cleaned_data:
                paciente.fecha_salida = form.cleaned_data['fecha_salida']
            paciente.save()
            return redirect('listar_pacientes')
    else:
        form = PacienteForm(instance=paciente) 

    return render(request, 'patient/edit.html', {'form': form, 'paciente': paciente})

# Eliminar un paciente
def eliminar_paciente(request, pk):
    try:
        paciente = Paciente.objects.get(id=pk)
    except Paciente.DoesNotExist:
        return redirect('enfermero_list')

    if request.method == 'POST':
        paciente.delete() 
        return redirect('listar_pacientes')  
    
    return render(request, 'patient/delete.html', {'paciente': paciente})

# M E D I C A M E N T O S

# Vista para crear un nuevo medicamento
def crear_medicamento(request):
    if request.method == 'POST':
        form = MedicamentoForm(request.POST)
        if form.is_valid():
            medicamento = Medicamento(
                nombre_medicamento=form.cleaned_data['nombre_medicamento'],
                ingrediente_activo=form.cleaned_data['ingrediente_activo'],
                componentes=form.cleaned_data['componentes'],
                estatus=form.cleaned_data['estatus']
            )
            medicamento.save()
            return redirect('listar_medicamentos')
    else:
        form = MedicamentoForm()
    
    return render(request, 'medicine/create.html', {'form': form})

# Vista para listar todos los medicamentos
def listar_medicamentos(request):
    medicamentos = Medicamento.objects.all()
    return render(request, 'medicine/list.html', {'medicamentos': medicamentos})

# Vista para editar un medicamento existente
def editar_medicamento(request, pk):
    try:
        medicamento = Medicamento.objects.get(pk=pk)
    except DoesNotExist:
        return redirect('listar_medicamentos')
    
    if request.method == 'POST':
        form = MedicamentoForm(request.POST)
        if form.is_valid():
            medicamento.nombre_medicamento = form.cleaned_data['nombre_medicamento']
            medicamento.ingrediente_activo = form.cleaned_data['ingrediente_activo']
            medicamento.componentes = form.cleaned_data['componentes']
            medicamento.estatus = form.cleaned_data['estatus']
            medicamento.save()  
            return redirect('listar_medicamentos')
    else:
        initial_data = {
            'nombre_medicamento': medicamento.nombre_medicamento,
            'ingrediente_activo': medicamento.ingrediente_activo,
            'componentes': medicamento.componentes,
            'estatus': medicamento.estatus
        }
        form = MedicamentoForm(initial=initial_data)
    
    return render(request, 'medicine/edit.html', {'form': form, 'medicamento': medicamento})

def eliminar_medicamento(request, pk):
    try:
        medicamento = Medicamento.objects.get(id=pk)
    except Medicamento.DoesNotExist:
        return redirect('listar_medicamentos')

    if request.method == 'POST':
        medicamento.delete()  
        return redirect('listar_medicamentos') 
    
    return render(request, 'medicine/delete.html', {'medicamento': medicamento})

# H O R A R I O S

# Crear horario
def crear_horario(request):
    if request.method == 'POST':
        form = HorarioPastilleroForm(request.POST)
        if form.is_valid():
            try:
                pastillero_id = form.cleaned_data['pastillero']
                medicamento_id = form.cleaned_data['medicamento']

                pastillero = Pastillero.objects.get(id=pastillero_id)
                medicamento = Medicamento.objects.get(id=medicamento_id)

                hora_inicio = form.cleaned_data['hora_inicio']
                hora_fin = form.cleaned_data['hora_fin']

                nuevo_horario = HorarioPastillero(
                    pastillero=pastillero,
                    medicamento=medicamento,
                    dosis=form.cleaned_data['dosis'],
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin,
                    dias=form.cleaned_data['dias']
                )
                nuevo_horario.save()

                return redirect('listar_horarios')

            except Exception as e:
                form.add_error(None, f"Error: {e}")
                return render(request, 'schedule/create.html', {'form': form})
    else:
        form = HorarioPastilleroForm()

    return render(request, 'schedule/create.html', {'form': form})

# Listar horario existentes
def listar_horarios(request):
    horarios = HorarioPastillero.objects.all()
    return render(request, 'schedule/list.html', {'horarios': horarios})

# Editar horarios
def editar_horario(request, pk):
    try:
        horario = HorarioPastillero.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return redirect('listar_horarios')

    if request.method == 'POST':
        form = HorarioPastilleroForm(request.POST)
        if form.is_valid():
            horario.pastillero = Pastillero.objects.get(id=form.cleaned_data['pastillero'])
            horario.hora_inicio = form.cleaned_data['hora_inicio']
            horario.hora_fin = form.cleaned_data['hora_fin']
            horario.dosis = form.cleaned_data['dosis']
            horario.dias = form.cleaned_data['dias']
            horario.save()
            return redirect('listar_horarios')
    else:
        initial_data = {
            'pastillero': horario.pastillero.id,
            'hora_inicio': horario.hora_inicio,
            'hora_fin': horario.hora_fin,
            'dosis': horario.dosis,
            'dias': horario.dias
        }
        form = HorarioPastilleroForm(initial=initial_data)

    return render(request, 'schedule/edit.html', {'form': form, 'horario': horario})


def eliminar_horario(request, pk):
    try:
        horario = HorarioPastillero.objects.get(id=pk)
    except HorarioPastillero.DoesNotExist:
        return redirect('listar_horarios')

    if request.method == 'POST':
        horario.delete()  
        return redirect('listar_horarios') 
    
    return render(request, 'schedule/delete.html', {'horario': horario})

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Pastillero, Medicamento, HorarioPastillero

@csrf_exempt  
def esp32_endpoint(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pastillero_id = data.get('pastillero_id')
            medicamento = data.get('medicamento')
            estado = data.get('estado')
            hora = data.get('hora')

            pastillero = Pastillero.objects.get(id=pastillero_id)
            medicamento_obj = Medicamento.objects.get(nombre_medicamento=medicamento)

            horario = HorarioPastillero.objects.create(
                pastillero=pastillero,
                medicamento=medicamento_obj,
                estado=estado,
                hora=hora
            )

            return JsonResponse({'status': 'success', 'message': 'Datos recibidos correctamente'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    else:
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'})

