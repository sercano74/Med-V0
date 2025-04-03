from django.utils import timezone
from django import forms
from .models import *
from A10_Usu.models import *


class HoraMedicaForm(forms.ModelForm):
    class Meta:
        model   = HoraMedica
        fields  = ['medico', 'f_hra', 'costo']
        widgets = {
            'medico'    : forms.Select(),
            'f_hra'    : forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            }

class EditarHoraMedicaForm(forms.ModelForm):
    class Meta:
        model = HoraMedica
        fields = ['medico', 'costo', 'f_hra','paciente','estado']
        widgets = {
            'medico'    : forms.Select(),
            'f_hra': forms.DateTimeInput(attrs={'type': 'datetime-local'}), # Widget para selector de fecha y hora
            'paciente'  : forms.Select(),
            'estado'    : forms.Select(choices=[('Disponible','Disponible'),('Tomada','Tomada'),('Anulada','Anulada')]),
        }

class SolicitarHoraForm(forms.Form):
    especialidad = forms.ModelChoiceField(queryset=Especialidad.objects.all(), label="Especialidad")
    medico = forms.ModelChoiceField(queryset=Medico.objects.none(), label="Médico", required=False, to_field_name='user_id')
    hora_medica = forms.ModelChoiceField(queryset=HoraMedica.objects.none(), label="Hora Médica", widget=forms.RadioSelect, required=False)

    def __init__(self, *args, **kwargs):
        especialidad_id = kwargs.pop('especialidad_id', None)
        medico_user_id = kwargs.pop('medico_user_id', None)
        super().__init__(*args, **kwargs)
        if especialidad_id:
            self.fields['medico'].queryset = Medico.objects.filter(
                especialidad=especialidad_id,
                medico_horas__estado='libre',
                medico_horas__f_hra__gt=timezone.now()
            ).distinct()
            self.fields['medico'].label_from_instance = lambda obj: f"{obj.user.first_name} {obj.user.last_name}"
        if medico_user_id:
            self.fields['hora_medica'].queryset = HoraMedica.objects.filter(
                medico__user_id=medico_user_id,
                estado='libre',
                f_hra__gt=timezone.now()  # Solo horas futuras
            )
            self.fields['hora_medica'].label_from_instance = lambda obj: f"{obj.id} / {obj.f_hra}"

    def clean(self):
        cleaned_data = super().clean()
        especialidad = cleaned_data.get("especialidad")
        medico = cleaned_data.get("medico")
        hora_medica = cleaned_data.get("hora_medica")

        if especialidad and not medico:
            self.add_error('medico', 'Debe seleccionar un médico.')
        if medico and not hora_medica:
            self.add_error('hora_medica', 'Debe seleccionar una hora médica.')