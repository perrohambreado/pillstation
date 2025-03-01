from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from .models import UserForm
from pymongo import MongoClient

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
        return redirect('login')
    
    username = request.session['username']
    return render(request, 'home.html', {'username': username})

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

