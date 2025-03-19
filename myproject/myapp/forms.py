from django import forms
from .models import Paciente, Medicamento, Enfermero, Pastillero, User, Administrador
from django.contrib.auth.hashers import make_password
from datetime import datetime
from mongoengine import queryset
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()  # Obtiene tu modelo de usuario personalizado

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'telefono', 'tipo_usuario']

# A D M I N I S T R A D O R

class AdministradorForm(forms.ModelForm):
    class Meta:
        model = Administrador
        fields = ['departamento', 'nivel_acceso']

# E N F E R M E R O

class EnfermeroForm(forms.ModelForm):
    pastilleros = forms.MultipleChoiceField(required=False)
    
    class Meta:
        model = Enfermero
        fields = [
            'nombre', 
            'apellidos', 
            'nfc_id', 
            'turno', 
            'activo', 
            'estatus',
        ]
        
    def __init__(self, *args, **kwargs):
        super(EnfermeroForm, self).__init__(*args, **kwargs)
        # Hacer los campos nombre y apellidos obligatorios
        self.fields['nombre'].required = True
        self.fields['apellidos'].required = True

class PacienteForm(forms.Form):
    fecha_ingreso = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    fecha_de_salida = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        
        if instance:

            if isinstance(instance, Paciente):
                for field in self.fields:
                    if hasattr(instance, field):
                        self.fields[field].initial = getattr(instance, field, None)
        else:

            self.fields['fecha_ingreso'].initial = datetime.now()
            self.fields['fecha_de_salida'].initial = None

class MedicamentoForm(forms.Form):
    nombre_medicamento = forms.CharField(max_length=255, label="Nombre del Medicamento", widget=forms.TextInput(attrs={'class': 'form-control'}))
    ingrediente_activo = forms.CharField(max_length=255, label="Ingrediente Activo", widget=forms.TextInput(attrs={'class': 'form-control'}))
    componentes = forms.CharField(required=False, label="Componentes", widget=forms.Textarea(attrs={'class': 'form-control'}))
    estatus = forms.BooleanField(required=False, label="Activo", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

class HorarioPastilleroForm(forms.Form):
    pastillero = forms.ChoiceField(choices=[], required=True) 
    medicamento = forms.ChoiceField(choices=[], required=True)  
    dosis = forms.IntegerField(required=True)
    hora_inicio = forms.TimeField(widget=forms.TimeInput(format='%H:%M'), required=True)
    hora_fin = forms.TimeField(widget=forms.TimeInput(format='%H:%M'), required=True)
    dias = forms.MultipleChoiceField(
        label="Días",
        choices=[('Lunes', 'Lunes'), ('Martes', 'Martes'), ('Miércoles', 'Miércoles'),
                 ('Jueves', 'Jueves'), ('Viernes', 'Viernes'), ('Sábado', 'Sábado'), ('Domingo', 'Domingo')],
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        super(HorarioPastilleroForm, self).__init__(*args, **kwargs)
        try:
            pastilleros = Pastillero.objects.all()
            self.fields['pastillero'].choices = [(str(p.id), p.codigo) for p in pastilleros] 

            medicamentos = Medicamento.objects.all()
            self.fields['medicamento'].choices = [(str(m.id), m.nombre_medicamento) for m in medicamentos]  
        except Exception as e:
            self.fields['medicamento'].choices = []
            self.fields['pastillero'].choices = []
            print(f"Error al cargar medicamentos o pastilleros: {e}")