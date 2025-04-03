from django import forms
from .models import *

class RegistroFichaMedicaForm(forms.ModelForm):
    class Meta:
        model = FichaMedica
        fields = '__all__'
        widgets = {
            'medico'    : forms.Select(),
            'paciente'  : forms.Select(),
            'f_consulta': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'estado': forms.Select(choices=[('Abierta', 'Abierta'), ('Cerrada', 'Cerrada')]),
            }