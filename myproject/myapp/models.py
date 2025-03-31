from django.db import models
from django import forms
from mongoengine import Document, EmailField, BooleanField, DateTimeField, fields, NULLIFY, CASCADE, StringField, ReferenceField, IntField, ListField
from django.contrib.auth.models import AbstractUser
from datetime import datetime    
from django.conf import settings

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
    meta = {'strict': False} 
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
        from myapp.models import Pastillero, EnfermeroMongo
        enfermero_mongo = EnfermeroMongo.objects(usuario_id=self.usuario.id).first()
        if not enfermero_mongo:
            return []
        pastilleros = Pastillero.objects(enfermeros_autorizados=enfermero_mongo)
        return pastilleros

    class Meta:
        db_table = 'enfermeros'

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"

# Enfermero - Modelo espejo MongoDB   
class EnfermeroMongo(Document):
    usuario_id = IntField(required=True, unique=True)  # Relación con el usuario en SQLite
    username = StringField(max_length=50)
    email = EmailField()
    nombre = StringField(max_length=100)
    apellidos = StringField(max_length=150)
    nfc_id = StringField(max_length=50, unique=True)
    turno = StringField(max_length=10, choices=["Matutino", "Vespertino", "Nocturno"])
    activo = BooleanField(default=True)
    fecha_registro = DateTimeField()
    estatus = BooleanField(default=True)
    telefono_cel = StringField(max_length=15)
    pastilleros_autorizados = ListField(StringField(), default=[])  # Almacena códigos de pastilleros

    meta = {'collection': 'Enfermero', 'strict': False} 


class EnfermeroPastillero(models.Model):
    enfermero = models.ForeignKey(Enfermero, on_delete=models.CASCADE, related_name='pastilleros')
    pastillero_id = models.CharField(max_length=24)  # ID del pastillero en MongoDB
    
    class Meta:
        db_table = 'enfermero_pastillero'
        unique_together = ('enfermero', 'pastillero_id')
    
    def __str__(self):
        return f"{self.enfermero} - Pastillero {self.pastillero_id}"
    
from mongoengine import Document, fields, ReferenceField, StringField, ListField, DictField, BooleanField

    
class Medicamento(Document):
    nombre_medicamento = StringField(max_length=100)
    ingrediente_activo = StringField(max_length=100)
    componentes = ListField(StringField())
    estatus = StringField(max_length=50)
    
    meta = {
        'db_alias': 'default',
        'collection': 'Medicamento'
    }
    
    @property
    def id(self):
        return self.pk

class Pastillero(Document):
    codigo = fields.StringField(max_length=100, unique=True)
    ubicacion = fields.DictField(default={
        "edificio": "",
        "piso": None,
        "area": "",
        "cama": ""
    })
    datos_sensores = fields.DictField(default={
        'humedad': None, 
        'temperatura': None, 
        'proximidad': None
    })
    enfermeros_autorizados = ListField(ReferenceField('EnfermeroMongo'), default=[])
    estado = fields.DictField(default={
        'activo': True,
        'ultima_apertura': datetime.min.isoformat(), 
        'ultimo_enfermero': None
    })
    logs_acceso = ListField(DictField(default={
        'fechaHora': None,
        'enfermero_id': '',
        'tipo_acceso': ''
    }), default=[])
    medicamentos = ListField(ReferenceField('Medicamento'), default=[])
    paciente = ReferenceField('Paciente', null=True)
    
    meta = {
        'db_alias': 'default',
        'collection': 'Pastillero'
    }
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'codigo': self.codigo if hasattr(self, 'codigo') else '',
            'ubicacion': self.ubicacion,
            'datos_sensores': self.datos_sensores,
            'estado': {
                'activo': self.estado.get('activo', False),
                'ultima_apertura': self.format_fecha(self.estado.get('ultima_apertura')),  
                'ultimo_enfermero': str(self.estado.get('ultimo_enfermero')) if self.estado.get('ultimo_enfermero') else None
            },
            'paciente': str(self.paciente.id) if self.paciente else None,
            'enfermeros_autorizados': [str(enfermero.id) for enfermero in self.enfermeros_autorizados if enfermero],
            'medicamentos': [str(med.id) for med in self.medicamentos if med]
        }
    
    def format_fecha(self, fecha):
        if isinstance(fecha, str):
            try:
                fecha = datetime.fromisoformat(fecha)
            except ValueError:
                return None
        return fecha.strftime("%Y-%m-%d %H:%M:%S") if fecha else None
    
    def get_medicamentos_details(self):
        return [
            {
                'id': str(med.id),
                'nombre_medicamento': med.nombre_medicamento if hasattr(med, 'nombre_medicamento') else '',
                'ingrediente_activo': med.ingrediente_activo if hasattr(med, 'ingrediente_activo') else '',
                'componentes': med.componentes if hasattr(med, 'componentes') else [],
                'estatus': med.estatus if hasattr(med, 'estatus') else ''
            } for med in self.medicamentos if med
        ]

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

# Poner el pastillero
    
# Create your models here.
class UserForm(forms.Form):
    username = forms.CharField(max_length=15)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

