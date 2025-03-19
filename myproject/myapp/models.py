from django.db import models
from django import forms
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from mongoengine import Document, EmailField, BooleanField, DateTimeField, fields, NULLIFY, CASCADE, StringField, ReferenceField, IntField, ListField
from django.contrib.auth.models import AbstractUser
from datetime import datetime    


# U S U A R I O S

class User(AbstractUser):
    telefono = models.CharField(max_length=15, blank=True, null=True)
    tipo_usuario = models.CharField(max_length=20, choices=[
        ('admin', 'Administrador'),
        ('enfermero', 'Enfermero')
    ])
    
    class Meta:
        db_table = 'usuarios'
        
    def __str__(self):
        return f"{self.username} ({self.get_tipo_usuario_display()})"


# A M I N I S T R A D O R
from django.conf import settings


# Administrador - Modelo SQLite
class Administrador(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin')
    departamento = models.CharField(max_length=100, blank=True, null=True)
    nivel_acceso = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'administradores'
        
    def __str__(self):
        return self.usuario.username

# Administrador - Modelo espejo MongoDB
class MongoAdministrador(Document):
    usuario_id = IntField(primary_key=True)  # ID del usuario en SQLite
    username = StringField(max_length=150)
    email = EmailField()
    password = StringField(max_length=255)
    is_active = BooleanField(default=True)
    fecha_registro = DateTimeField()
    departamento = StringField(max_length=100, null=True)
    nivel_acceso = IntField(default=1)
    telefono = StringField(max_length=15, null=True)

    meta = {'collection': 'Administrador'}

    def __str__(self):
        return self.username

# E N F E R M E R O S

# Enfermero - Modelo SQLite
class Enfermero(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enfermero')
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=150)
    nfc_id = models.CharField(max_length=50, unique=True)
    turno = models.CharField(max_length=10, choices=[
        ("Matutino", "Matutino"), 
        ("Vespertino", "Vespertino"), 
        ("Nocturno", "Nocturno")
    ])
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estatus = models.BooleanField(default=True)
    telefono_cel = models.CharField(max_length=15)

    def get_pastilleros(self):
        from myapp.models import Pastillero  # Importa el modelo de MongoDB
        pastillero_ids = self.pastilleros.values_list('pastillero_id', flat=True)
        return Pastillero.objects(id__in=pastillero_ids)

    class Meta:
        db_table = 'enfermeros'
    
    def __str__(self):
        return f"{self.nombre} {self.apellidos}"

    
from mongoengine import Document, EmailField, fields, StringField, ReferenceField, IntField, ListField, EmailField, BooleanField
    
class EnfermeroMongo(Document):
    usuario_id = IntField(required=True, unique=True)
    username = StringField(max_length=50)
    email = EmailField()
    password = StringField(max_length=255)
    nombre = StringField(max_length=100)
    apellidos = StringField(max_length=150)
    nfc_id = StringField(max_length=50, unique=True)
    turno = StringField(max_length=10, choices=["Matutino", "Vespertino", "Nocturno"])
    activo = BooleanField(default=True)
    fecha_registro = DateTimeField()
    estatus = BooleanField(default=True)
    telefono_cel = StringField(max_length=15)
    pastilleros_autorizados = ListField(IntField(), default=[])
    
    meta = {'collection': 'Enfermero'}
    
    def __str__(self):
        return f"{self.nombre} {self.apellidos}"

# Relación Enfermero-Pastillero (SQLite)
class EnfermeroPastillero(models.Model):
    enfermero = models.ForeignKey(Enfermero, on_delete=models.CASCADE, related_name='pastilleros')
    pastillero_id = models.CharField(max_length=24)  # ID del pastillero en MongoDB
    
    class Meta:
        db_table = 'enfermero_pastillero'
        unique_together = ('enfermero', 'pastillero_id')


# P A S T I L L E R O S
class Ubicacion(Document):
    edificio = fields.StringField(max_length=100)
    piso = fields.IntField()
    area = fields.StringField(max_length=100)
    cama = fields.StringField(max_length=50)

    meta = {
        'abstract': True
    }

# Enfermero asociado

class SensorData(Document):
    Humedad = fields.IntField()
    Temperatura = fields.IntField()
    Proximidad = fields.IntField()

    meta = {
        'abstract': True
    }

class EstadoPastillero(Document):
    activo = fields.BooleanField(default=True)
    ultima_apertura = fields.DateTimeField(default=datetime.now)
    ultimo_enfermero = fields.ReferenceField('EnfermeroMongo', reverse_delete_rule=NULLIFY)  
    nivel_bateria = fields.IntField(default=100)

    meta = {
        'abstract': True
    }


class LogAcceso(Document):
    fechaHora = fields.DateTimeField(default=datetime.now)
    nfc_id = fields.StringField(max_length=100)
    tipo_acceso = fields.StringField(max_length=20, choices=["apertura", "cierre"])

    meta = {
        'abstract': True
    }


class Pastillero(Document):
    codigo = fields.StringField(max_length=100, unique=True)
    ubicacion = fields.DictField()  # Reemplazo de JSONField
    Datos_Sensores = fields.ListField(fields.DictField(), default=[])
    enfermeros_autorizados = fields.ListField(fields.ReferenceField('EnfermeroMongo'), default=[])
    estado = fields.DictField()  # Reemplazo de JSONField
    logs_acceso = fields.ListField(fields.DictField(), default=[])

    meta = {
        'db_alias': 'default',
        'collection': 'Pastillero'
    }

# Dosis
# poner los medicamentos
# Poner los medicamenteos
# Medicamento
class HorarioPastillero(Document):
    pastillero = ReferenceField('Pastillero', required=True)
    medicamento = ReferenceField('Medicamento', required=True)
    dosis = IntField(required=True)
    hora_inicio = StringField(required=True)  
    hora_fin = StringField(required=True)   
    dias = ListField(StringField(), required=True) 

    meta = {'collection': 'HorarioPastillero'}
    
# P A C I E N T E S

class Paciente(Document):
    fecha_ingreso = fields.DateTimeField(default=datetime.now)
    fecha_de_salida = fields.DateTimeField(null=True, blank=True)

    meta = {
        'db_alias': 'default',
        'collection': 'Paciente'
    }

# meter pastillero

# M E D I C A M E N T O

class Medicamento(Document):
    nombre_medicamento = fields.StringField(max_length=255)
    ingrediente_activo = fields.StringField(max_length=255)
    componentes = fields.StringField(null=True, blank=True)
    estatus = fields.BooleanField(default=True)

    meta = {
        'db_alias': 'default',
        'collection': 'Medicamento'
    }

# Poner el pastillero


    
# Create your models here.
class UserForm(forms.Form):
    username = forms.CharField(max_length=15)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

