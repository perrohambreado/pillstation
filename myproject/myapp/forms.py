from django import forms
from .models import Paciente, Medicamento, Horario

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