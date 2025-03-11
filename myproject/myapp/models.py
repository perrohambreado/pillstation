from django.db import models
from django import forms
from datetime import datetime
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from mongoengine import Document, fields, NULLIFY, CASCADE, StringField, DateTimeField, ReferenceField, IntField, ListField

# E N F E R M E R O S

from mongoengine import Document, fields
from django.contrib.auth.hashers import make_password

class Enfermero(Document):
    nombre = fields.StringField(max_length=100)
    apellidos = fields.StringField(max_length=150)
    nfc_id = fields.StringField(max_length=50, unique=True)
    turno = fields.StringField(max_length=10, choices=["Matutino", "Vespertino", "Nocturno"])
    activo = fields.BooleanField(default=True)
    fecha_registro = fields.DateTimeField(auto_now_add=True)
    pastilleros_autorizados = fields.ListField(fields.ReferenceField('Pastillero'), default=[])
    usuario = fields.StringField(max_length=50, unique=True)
    password = fields.StringField(max_length=255)
    estatus = fields.BooleanField(default=True)
    email = fields.EmailField(unique=True)
    TelefonoCel = fields.StringField(max_length=15)

    def save(self, *args, **kwargs):
        if not self.pk or "password" in kwargs:
            self.password = make_password(self.password)  
        super().save(*args, **kwargs)

    meta = {'collection': 'Enfermero'}


# P A S T I L L E R O S
class Ubicacion(Document):
    edificio = fields.StringField(max_length=100)
    piso = fields.IntField()
    area = fields.StringField(max_length=100)
    cama = fields.StringField(max_length=50)

    meta = {
        'abstract': True
    }


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
    ultimo_enfermero = fields.ReferenceField('Enfermero', reverse_delete_rule=NULLIFY)  
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
    enfermeros_autorizados = fields.ListField(fields.ReferenceField('Enfermero'), default=[])
    estado = fields.DictField()  # Reemplazo de JSONField
    logs_acceso = fields.ListField(fields.DictField(), default=[])

    meta = {
        'db_alias': 'default',
        'collection': 'Pastillero'
    }

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
    
# Create your models here.
class UserForm(forms.Form):
    username = forms.CharField(max_length=15)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

#DATOS DEL PASTILLERO
class PillStation(models.Model):
    ultrasonico = models.BooleanField(default=True)
    temperatura = models.CharField(max_length=20)
    humedad = models.CharField(max_length=20)
    hora = models.PositiveSmallIntegerField()
    minutos = models.PositiveSmallIntegerField()

#class Paciente(models.Model):
#    nombre = models.CharField(max_length=100)
#    edad = models.IntegerField()
#    telefono = models.CharField(max_length=15)

#    def __str__(self):
#        return self.nombre
    
#class Medicamento(models.Model):
#    nombre = models.CharField(max_length=100)
#    dosis = models.CharField(max_length=50)
#    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)

#    def __str__(self):
#        return self.nombre
    

#class Horario(models.Model):
#    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE)
#    hora = models.TimeField()

#    def __str__(self):
#        return f"{self.medicamento.nombre} a las {self.hora}"

#class Pastillero(models.Model):
#    estado = models.CharField(max_length=50)
#    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)

#    def __str__(self):
#        return f"Pastillero de {self.paciente.nombre} - {self.estado}" 