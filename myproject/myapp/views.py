from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from .models import UserForm
from pymongo import MongoClient
from .models import Paciente
from .forms import PacienteForm

client = MongoClient("mongodb+srv://regina:pKW6Ir1kXLapHf5u@pillstation.c4ue9.mongodb.net/?retryWrites=true&w=majority&appName=PillStation")
db = client["PillStation"]

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

def index(request):
    return render(request, 'index.html')

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

