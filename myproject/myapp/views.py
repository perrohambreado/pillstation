from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from .models import UserForm, EnfermeroMongo, Enfermero, Paciente, Medicamento, Pastillero, HorarioPastillero, Administrador
from .forms import AdministradorForm, EnfermeroForm, PacienteForm, MedicamentoForm, HorarioPastilleroForm, CustomUserCreationForm
from pymongo import MongoClient
from mongoengine.errors import DoesNotExist
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from .signals import sync_nurse_to_mongo, sync_admin_to_mongo, eliminar_admin_de_mongo, eliminar_enfermero_de_mongo, sync_pastillero_relation   
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET

client = MongoClient("mongodb+srv://regina:pKW6Ir1kXLapHf5u@pillstation.c4ue9.mongodb.net/?retryWrites=true&w=majority&appName=PillStation")
db = client["PillStation"]

# S E S I O N

# Vista para login
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            if user.tipo_usuario == 'admin':
                return redirect('admin_select_dashboard') 
            elif user.tipo_usuario == 'enfermero':
                return redirect('enfermero_dashboard')  
            else:
                return redirect('home')
        else:
            return HttpResponse('Credenciales no válidas', status=401)
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

# Vista para logout
def logout_view(request):
    logout(request)
    return redirect('login') 

# Vista para que el administrador elija qué listar

@login_required


def admin_select_dashboard(request):
    if request.user.tipo_usuario != 'admin':
        return HttpResponseForbidden("Acceso denegado")
    
    return render(request, 'admin_select_dashboard.html')

# D A S H B O A R D  A D M I N

# Vista del dashboard para el Administrador
@login_required
def admin_dashboard(request):
    if not request.user.admin:
        return HttpResponseForbidden("Acceso denegado")
    
    return render(request, 'admin_dashboard.html')

# Crear administrador
User = get_user_model()

def crear_administrador(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        admin_form = AdministradorForm(request.POST)
        
        if user_form.is_valid() and admin_form.is_valid():
            username = user_form.cleaned_data['username']
            
            if User.objects.filter(username=username).exists():
                usuario_existente = User.objects.get(username=username)
                if hasattr(usuario_existente, 'administrador'):
                    admin_form.add_error('usuario', 'Este usuario ya tiene un administrador asignado.')
                    messages.error(request, 'Error: Este usuario ya tiene un administrador.')
                    return render(request, 'admin/create.html', {'user_form': user_form, 'admin_form': admin_form})
                
                usuario_existente.is_staff = True
                usuario_existente.is_superuser = True
                usuario_existente.tipo_usuario = 'admin'
                usuario_existente._skip_signal = True
                usuario_existente.save()
                
                nuevo_administrador = admin_form.save(commit=False)
                nuevo_administrador.usuario = usuario_existente
                nuevo_administrador.save()
                messages.success(request, 'Administrador creado exitosamente.')
                
                return redirect('listar_administradores')
            
            nuevo_usuario = user_form.save(commit=False)
            nuevo_usuario.tipo_usuario = 'admin'
            nuevo_usuario.is_staff = True
            nuevo_usuario.is_superuser = True
            nuevo_usuario.save()
            
            nuevo_usuario._skip_signal = True
            nuevo_usuario.save()
            
            nuevo_administrador = admin_form.save(commit=False)
            nuevo_administrador.usuario = nuevo_usuario
            nuevo_administrador.save()
            
            sync_admin_to_mongo(nuevo_administrador)
            
            messages.success(request, 'Administrador creado exitosamente.')
            return redirect('listar_administradores')
        else:
            print("Errores en user_form:", user_form.errors)
            print("Errores en admin_form:", admin_form.errors)
            messages.error(request, 'Error al crear el administrador.')
    else:
        user_form = CustomUserCreationForm()
        admin_form = AdministradorForm()
    
    return render(request, 'admin/create.html', {'user_form': user_form, 'admin_form': admin_form})

# Editar administrador 
def editar_administrador(request, pk):
    try:
        administrador = Administrador.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return redirect('listar_administradores')

    user = administrador.usuario

    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST, instance=user)
        admin_form = AdministradorForm(request.POST, instance=administrador)
        
        if user_form.is_valid() and admin_form.is_valid():
            user = user_form.save()

            administrador = admin_form.save(commit=False)
            administrador.usuario = user
            administrador.save()

            return redirect('listar_administradores')
    else:
        user_form = CustomUserCreationForm(instance=user)
        admin_form = AdministradorForm(instance=administrador)

    return render(request, 'admin/edit.html', {'user_form': user_form, 'admin_form': admin_form, 'administrador': administrador})

# Listar administradores
def listar_administradores(request):
    administradores = Administrador.objects.all()
    return render(request, 'admin/list.html', {'administradores': administradores})

# Eliminar administrador
def eliminar_administrador(request, pk):
    try:
        administrador = Administrador.objects.get(id=pk)
    except Administrador.DoesNotExist:
        return redirect('listar_administradores')

    usuario = administrador.usuario

    if request.method == 'POST':

        eliminar_admin_de_mongo(usuario.id) 
        administrador.delete()

        usuario.delete()

        return redirect('listar_administradores')

    return render(request, 'admin/delete.html', {'administrador': administrador})

# D A S H B O A R D  N U R S E

# Vista del dashboard para el Administrador
@login_required
def nurse_dashboard(request):
    if not request.user.is_staff: 
        return HttpResponseForbidden("Acceso denegado")
    
    return render(request, 'nurse_dashboard.html')

# Crear enfermero
User = get_user_model()

def crear_enfermero(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        enfermero_form = EnfermeroForm(request.POST)

        if user_form.is_valid() and enfermero_form.is_valid():
            username = user_form.cleaned_data['username']

            if User.objects.filter(username=username).exists():
                usuario_existente = User.objects.get(username=username)
                if hasattr(usuario_existente, 'enfermero'):
                    enfermero_form.add_error('usuario', 'Este usuario ya tiene un enfermero asignado.')
                    messages.error(request, 'Error: Este usuario ya tiene un enfermero.')
                    return render(request, 'nurse/create.html', {'user_form': user_form, 'enfermero_form': enfermero_form})

                usuario_existente.is_staff = True
                usuario_existente.save()

                nuevo_enfermero = enfermero_form.save(commit=False)
                nuevo_enfermero.usuario = usuario_existente
                nuevo_enfermero.save()
                messages.success(request, 'Enfermero creado Existosamente') 
                return redirect('listar_enfermeros')     
            
            nuevo_usuario = user_form.save(commit=False)
            nuevo_usuario.tipo_usuario = 'enfermero' 
            nuevo_usuario.is_staff = True
            nuevo_usuario.is_superuser = False 
            nuevo_usuario.save()

            nuevo_usuario._skip_signal = True
            nuevo_usuario.save()

            nuevo_enfermero = enfermero_form.save(commit=False)   
            nuevo_enfermero.usuario = nuevo_usuario
            nuevo_enfermero.save()  

            sync_nurse_to_mongo(nuevo_enfermero)

            messages.success(request, 'Enfermero creado exitosamente.')
            return redirect('listar_enfermeros')
        else:
            print("Errores en user_form:", user_form.errors)
            print("Errores en enfermero_form:", enfermero_form.errors)
            messages.error(request, 'Error al crear el administrador.')
    else:
        user_form = CustomUserCreationForm()
        enfermero_form = EnfermeroForm()
    
    return render(request, 'nurse/create.html', {'user_form': user_form, 'enfermero_form': enfermero_form})

# Editar enfermero
def editar_enfermero(request, pk):
    try:
        enfermero = Enfermero.objects.get(pk=pk)
    except Enfermero.DoesNotExist:
        return redirect('listar_enfermeros')

    user = enfermero.usuario

    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST, instance=user)
        enfermero_form = EnfermeroForm(request.POST, instance=enfermero)
        
        if user_form.is_valid() and enfermero_form.is_valid():
            user = user_form.save()

            enfermero = enfermero_form.save(commit=False)
            enfermero.usuario = user
            enfermero.save()

            return redirect('listar_enfermeros')
    else:
        user_form = CustomUserCreationForm(instance=user)
        enfermero_form = EnfermeroForm(instance=enfermero)

    return render(request, 'nurse/edit.html', {'user_form': user_form, 'enfermero_form': enfermero_form, 'enfermero': enfermero})

# Listar enfermeros
def listar_enfermeros(request):
    enfermeros = Enfermero.objects.all()
    return render(request, 'nurse/list.html', {'enfermeros': enfermeros})

# Eliminar enfermero
from django.shortcuts import render, redirect
from .models import Enfermero

def eliminar_enfermero(request, pk):
    try:
        enfermero = Enfermero.objects.get(id=pk)
    except Enfermero.DoesNotExist:
        return redirect('listar_enfermeros')

    usuario = enfermero.usuario

    if request.method == 'POST':

        eliminar_enfermero_de_mongo(usuario.id)
        enfermero.delete()

        usuario.delete()

        return redirect('listar_enfermeros')

    return render(request, 'nurse/delete.html', {'enfermero': enfermero})

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

def loginn(request):
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
    return render(request, 'home.html')


def aboutUs(request):
    return render(request, 'aboutUs.html')

def services(request):
    return render(request, 'services.html')

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

def add(request):
    if request.method == 'POST':
        user = request.POST['user']


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from .models import Enfermero, Pastillero
from bson import ObjectId

@login_required
def enfermero_dashboard(request):
    if not hasattr(request.user, 'enfermero'):
        messages.error(request, 'Acceso no autorizado. Necesitas ser un enfermero para acceder a esta página.')
        return redirect('home')
    
    enfermero = request.user.enfermero
    
    pastilleros = enfermero.get_pastilleros()
    
    context = {
        'enfermero': enfermero,
        'pastilleros': pastilleros
    }
    
    return render(request, 'enfermero/dashboard.html', context)

@login_required
@require_GET
def listar_pastilleros_disponibles(request):
    if not hasattr(request.user, 'enfermero'):
        messages.error(request, 'Acceso no autorizado. Necesitas ser un enfermero para acceder a esta página.')
        return redirect('home')
    
    from myapp.models import EnfermeroMongo
    enfermero_mongo = EnfermeroMongo.objects(usuario_id=request.user.id).first()
    
    pastilleros = Pastillero.objects().all()
    
    for p in pastilleros:
        if enfermero_mongo:
            enfermeros_ids = [str(ref.id) for ref in p.enfermeros_autorizados]
            p.asignado = str(enfermero_mongo.id) in enfermeros_ids
        else:
            p.asignado = False
    
    context = {
        'pastilleros': pastilleros
    }
    
    return render(request, 'enfermero/pastilleros_disponibles.html', context)

@login_required
@require_POST
def asignar_pastillero(request):
    if not hasattr(request.user, 'enfermero'):
        messages.error(request, 'Acceso no autorizado. Necesitas ser un enfermero para acceder a esta página.')
        return redirect('home')
    
    pastillero_id = request.POST.get('pastillero_id')
    
    if not pastillero_id:
        messages.error(request, 'ID de pastillero no proporcionado')
        return redirect('enfermero_dashboard')
    
    try:
        pastillero_id = str(ObjectId(pastillero_id))
    except:
        messages.error(request, 'ID de pastillero inválido')
        return redirect('enfermero_dashboard')
    
    success = sync_pastillero_relation(
        enfermero_id=request.user.enfermero.id,
        pastillero_id=pastillero_id,
        add=True
    )
    
    if success:
        messages.success(request, 'Pastillero asignado correctamente')
    else:
        messages.error(request, 'Error al asignar pastillero')
    
    return redirect('enfermero_dashboard')

@login_required
@require_POST
def desasignar_pastillero(request):
    if not hasattr(request.user, 'enfermero'):
        messages.error(request, 'Acceso no autorizado. Necesitas ser un enfermero para acceder a esta página.')
        return redirect('home')
    
    pastillero_id = request.POST.get('pastillero_id')
    
    if not pastillero_id:
        messages.error(request, 'ID de pastillero no proporcionado')
        return redirect('enfermero_dashboard')
    
    try:
        pastillero_id = str(ObjectId(pastillero_id))
    except:
        messages.error(request, 'ID de pastillero inválido')
        return redirect('enfermero_dashboard')
    
    success = sync_pastillero_relation(
        enfermero_id=request.user.enfermero.id,
        pastillero_id=pastillero_id,
        add=False
    )
    
    if success:
        messages.success(request, 'Pastillero desasignado correctamente')
    else:
        messages.error(request, 'Error al desasignar pastillero')
    
    return redirect('enfermero_dashboard')

@login_required
def ver_detalle_pastillero(request, pastillero_id):
    if not hasattr(request.user, 'enfermero'):
        messages.error(request, 'Acceso no autorizado. Necesitas ser un enfermero para acceder a esta página.')
        return redirect('home')
    try:
        enfermero_mongo = EnfermeroMongo.objects(usuario_id=request.user.id).first()
        if not enfermero_mongo:
            messages.error(request, 'No se encontró su perfil de enfermero')
            return redirect('enfermero_dashboard')
        pastillero = Pastillero.objects.get(id=pastillero_id)
        if pastillero.medicamentos:
            for i, med_ref in enumerate(pastillero.medicamentos):
                try:
                    medicamento = Medicamento.objects.get(id=med_ref.id)
                    pastillero.medicamentos[i] = medicamento
                except Exception as e:
                    print(f"Error al cargar medicamento: {e}")
        if pastillero.paciente:
            try:
                paciente = Paciente.objects.get(id=pastillero.paciente.id)
                pastillero.paciente = paciente
            except Exception as e:
                print(f"Error al cargar paciente: {e}")
        ultima_apertura = None
        enfermero_ultima_apertura = None
        if pastillero.estado.get('ultima_apertura') and pastillero.estado.get('ultima_apertura') != datetime.min.isoformat():
            ultima_apertura_datetime = datetime.fromisoformat(pastillero.estado['ultima_apertura'])
            ultima_apertura = {
                'fechaHora': ultima_apertura_datetime
            }
            if pastillero.estado.get('ultimo_enfermero'):
                try:
                    enfermero_ultima_apertura = EnfermeroMongo.objects.get(id=pastillero.estado['ultimo_enfermero'])
                except Exception as e:
                    print(f"Error al cargar enfermero de última apertura: {e}")
        elif pastillero.logs_acceso:
            logs_ordenados = sorted(pastillero.logs_acceso, 
                                  key=lambda x: x['fechaHora'] if x['fechaHora'] else datetime.min,
                                  reverse=True)
            ultima_apertura = logs_ordenados[0]  
            try:
                enfermero_ultima_apertura = EnfermeroMongo.objects.get(id=ultima_apertura['enfermero_id'])
            except Exception as e:
                print(f"Error al cargar enfermero de última apertura: {e}")
    except Exception as e:
        messages.error(request, f'Pastillero no encontrado: {str(e)}')
        return redirect('enfermero_dashboard')
    enfermeros_ids = [str(ref.id) for ref in pastillero.enfermeros_autorizados]
    if str(enfermero_mongo.id) not in enfermeros_ids:
        messages.error(request, 'No tienes acceso a este pastillero')
        return redirect('enfermero_dashboard')
    context = {
        'pastillero': pastillero,
        'ultima_apertura': ultima_apertura,
        'ultimo_enfermero': enfermero_ultima_apertura
    }
    return render(request, 'enfermero/detalle_pastillero.html', context)

@login_required
@require_GET
def api_pastilleros_disponibles(request):
    if not hasattr(request.user, 'enfermero'):
        return JsonResponse({'error': 'Acceso no autorizado'}, status=403)
    
    from myapp.models import EnfermeroMongo
    enfermero_mongo = EnfermeroMongo.objects(usuario_id=request.user.id).first()
    
    if not enfermero_mongo:
        return JsonResponse({'error': 'No se encontró su perfil de enfermero'}, status=404)
    
    pastilleros = Pastillero.objects.all()
    
    pastilleros_data = []
    for p in pastilleros:
        data = p.to_dict()
        enfermeros_ids = [str(ref.id) for ref in p.enfermeros_autorizados]
        data['asignado'] = str(enfermero_mongo.id) in enfermeros_ids
        pastilleros_data.append(data)
    
    return JsonResponse({'pastilleros': pastilleros_data})

@login_required
@require_POST
def api_asignar_pastillero(request):
    if not hasattr(request.user, 'enfermero'):
        return JsonResponse({'error': 'Acceso no autorizado'}, status=403)
    
    pastillero_id = request.POST.get('pastillero_id')
    
    if not pastillero_id:
        return JsonResponse({'error': 'ID de pastillero no proporcionado'}, status=400)
    
    try:
        pastillero_id = str(ObjectId(pastillero_id))
    except:
        return JsonResponse({'error': 'ID de pastillero inválido'}, status=400)
    
    success = sync_pastillero_relation(
        enfermero_id=request.user.enfermero.id,
        pastillero_id=pastillero_id,
        add=True
    )
    
    if success:
        return JsonResponse({'success': True, 'message': 'Pastillero asignado correctamente'})
    else:
        return JsonResponse({'error': 'Error al asignar pastillero'}, status=500)

@login_required
@require_POST
def api_desasignar_pastillero(request):
    if not hasattr(request.user, 'enfermero'):
        return JsonResponse({'error': 'Acceso no autorizado'}, status=403)
    
    pastillero_id = request.POST.get('pastillero_id')
    
    if not pastillero_id:
        return JsonResponse({'error': 'ID de pastillero no proporcionado'}, status=400)
    
    try:
        pastillero_id = str(ObjectId(pastillero_id))
    except:
        return JsonResponse({'error': 'ID de pastillero inválido'}, status=400)
    
    success = sync_pastillero_relation(
        enfermero_id=request.user.enfermero.id,
        pastillero_id=pastillero_id,
        add=False
    )
    
    if success:
        return JsonResponse({'success': True, 'message': 'Pastillero desasignado correctamente'})
    else:
        return JsonResponse({'error': 'Error al desasignar pastillero'}, status=500)