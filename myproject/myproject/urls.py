"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from myapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('home/', views.home, name='home'),
    path('logout/', views.logout, name='logout'),
    path('nurse/', views.listar_enfermeros, name='enfermero_list'), 
    path('crear/', views.crear_enfermero, name='crear_enfermero'),
    path('editar/<str:pk>/', views.editar_enfermero, name='editar_enfermero'),
    path('eliminar/<str:pk>/', views.eliminar_enfermero, name='eliminar_enfermero'),
    path('patient/', views.listar_pacientes, name='listar_pacientes'),
    path('paciente/crear/', views.crear_paciente, name='crear_paciente'),
    path('paciente/<str:pk>/editar/', views.editar_paciente, name='editar_paciente'),
    path('paciente/<str:pk>/eliminar/', views.eliminar_paciente, name='eliminar_paciente'),
    path('medicamento/crear/', views.crear_medicamento, name='crear_medicamento'),
    path('medicamento/<pk>/editar/', views.editar_medicamento, name='editar_medicamento'),
    path('medicamento/<pk>/eliminar/', views.eliminar_medicamento, name='eliminar_medicamento'),
    path('medicine/', views.listar_medicamentos, name='listar_medicamentos'),
    path('horario/crear/', views.crear_horario, name='crear_horario'),
    path('schedule/', views.listar_horarios, name='listar_horarios'),
    path('horario/<pk>/editar/', views.editar_horario, name='editar_horario'),
    path('horario/<pk>/eliminar/', views.eliminar_horario, name='eliminar_horario'),
    path('myapp/pastilleroAPI/', include('myapp.urls'))
]
