from django.urls import path
from . import views  # Importa las vistas de la aplicación

urlpatterns = [
    path('esp32/', views.esp32_endpoint, name='esp32_endpoint'),  
]
