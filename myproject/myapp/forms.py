from django import forms
from .models import Paciente, Medicamento, Enfermero, Pastillero
from django.contrib.auth.hashers import make_password
from datetime import datetime
from mongoengine import queryset

"""
class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['nombre', 'edad', 'telefono'] 

class MedicamentoForm(forms.ModelForm):
    class Meta:
        model = Medicamento
        fields = ['nombre', 'dosis', 'paciente'] 

class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = ['medicamento', 'hora']  

class MedicamentoForm(forms.ModelForm):
    class Meta:
        model = Medicamento
        fields = ['nombre', 'dosis', 'paciente']

class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = ['medicamento', 'hora']

class PastilleroForm(forms.ModelForm):
    class Meta:
        model = Pastillero
        fields = ['estado', 'paciente']

"""

class EnfermeroForm(forms.Form):
    nombre = forms.CharField(max_length=100)
    apellidos = forms.CharField(max_length=150)
    nfc_id = forms.CharField(max_length=50)
    turno = forms.ChoiceField(choices=[("Matutino", "Matutino"), 
                                      ("Vespertino", "Vespertino"), 
                                      ("Nocturno", "Nocturno")])
    activo = forms.BooleanField(required=False)
    usuario = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField()
    TelefonoCel = forms.CharField(max_length=15)
    
    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)  
        
        if instance:
            for field in self.fields:
                if hasattr(instance, field):
                    self.fields[field].initial = getattr(instance, field, None)


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