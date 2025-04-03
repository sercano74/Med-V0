# forms.py en gestion_usuarios
from django import forms

from A31_Con.models import Examen, Medicamento
from .models import *
from .utils import enviar_email_clave_provisoria,generar_clave_provisoria
from allauth.account.forms import SignupForm
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.models import Permission
from django.contrib.auth.password_validation import validate_password

import datetime as dt
from icecream import ic




#* ###############################################
#* #####     SELECTOR DE FORMS S/TIPO        #####
#* ###############################################
class SeleccionarTipoRegistroForm(forms.Form):
    TIPO_USUARIO_CHOICES = [
        ('paciente', 'Paciente'),
        ('jefeplataforma', 'Jefe de Plataforma'),
        # Agrega otros tipos de usuario si es necesario
    ]
    tipo_usuario = forms.ChoiceField(choices=TIPO_USUARIO_CHOICES, label="Seleccione el tipo de usuario")


#* ########################################
#* #####     FORM PARA PACIENTES      #####
#* ########################################
from django.contrib.auth import get_user_model

# User = get_user_model()

class PacienteSignupForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Paciente.objects.filter(user__email=email).exists(): #Validación de email existente
            raise forms.ValidationError("Este correo electrónico ya está registrado por otro paciente.")
        return email


class PacienteProfileForm(forms.ModelForm):
    # username = forms.CharField(label='Nombre de usuario', max_length=150)
    first_name = forms.CharField(label='Nombre', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Apellido', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    dni = forms.CharField(label='DNI', max_length=12, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    f_nacim = forms.DateField(label='Fecha de Nacimiento', required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    imagen = forms.ImageField(label='Imagen', required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    genero = forms.ModelChoiceField(queryset=Genero.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    tel_pers = forms.CharField(label='Teléfono Personal', max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    name_emerg = forms.CharField(label='Nombre de Emergencia', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    tel_emerg = forms.CharField(label='Teléfono de Emergencia', max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(label='Nueva contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    new_password2 = forms.CharField(label='Confirmar nueva contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)

    class Meta:
        model = Paciente
        fields = ['dni', 'f_nacim', 'imagen', 'genero', 'tel_pers', 'name_emerg', 'tel_emerg', 'grupoSangre', 'enfermedades', 'cirugias', 'alergias', 'meds_actuales', 'sistema_salud']
        widgets = {
            'grupoSangre': forms.Select(choices=Paciente.gruposSangre, attrs={'class': 'form-control'}),
            'sistema_salud': forms.Select(attrs={'class': 'form-control'}),
            'enfermedades': forms.Textarea(attrs={'class': 'form-control'}),
            'cirugias': forms.Textarea(attrs={'class': 'form-control'}),
            'alergias': forms.Textarea(attrs={'class': 'form-control'}),
            'meds_actuales': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        paciente = super().save(commit=False)
        user = paciente.user
        # user.username = self.cleaned_data['username']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.dni = self.cleaned_data['dni']
        user.f_nacim = self.cleaned_data['f_nacim']
        user.imagen = self.cleaned_data['imagen']
        user.genero = self.cleaned_data['genero']
        user.tel_pers = self.cleaned_data['tel_pers']
        user.name_emerg = self.cleaned_data['name_emerg']
        user.tel_emerg = self.cleaned_data['tel_emerg']
        if self.cleaned_data['new_password1']:
            user.set_password(self.cleaned_data['new_password1'])
        if commit:
            user.save()
            paciente.save()
        return paciente



#* ########################################
#* ########### TODOS LOS ROLES ############
#* ########################################
ROLE_CHOICES = [
    ('paciente', 'Paciente'),
    ('jefe_plataforma', 'Jefe de Plataforma'),
    ('recepcionista', 'Recepcionista'),
    ('medico', 'Medico'),
]

class GenericSignupForm(forms.Form):
    role = forms.ChoiceField(choices=ROLE_CHOICES, label='Rol')
    email = forms.EmailField(label='Correo electrónico')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(GenericSignupForm, self).__init__(*args, **kwargs)
        if user:
            # si el usuario es superuser podrá agregar a cualquier rol
            if user.is_superuser:
                self.fields['role'].choices = ROLE_CHOICES
            # si el usuario es jefe de plataforma tiene permisos para agregar a todos los roles
            elif user.has_perm('A10_Usu.add_paciente') and user.has_perm('A10_Usu.add_recepcionista') and user.has_perm ('A10_Usu.add_medico'):
                self.fields['role'].choices = [
                    ('paciente', 'Paciente'),
                    ('recepcionista', 'Recepcionista'),
                    ('medico', 'Medico'),
                ]
            # si el usuario es recepcionista, solo tiene permiso para agregar pacientes
            elif user.has_perm('A10_Usu.add_paciente'):
                self.fields['role'].choices = [
                    ('paciente', 'Paciente'),
                ]


class JefePlataformaProfileForm(forms.ModelForm):
    # username = forms.CharField(label='Nombre de usuario', max_length=150)
    first_name = forms.CharField(label='Nombre', max_length=150)
    last_name = forms.CharField(label='Apellido', max_length=150)
    dni = forms.CharField(label='DNI', max_length=12, required=False)
    f_nacim = forms.DateField(label='Fecha de Nacimiento', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    imagen = forms.ImageField(label='Imagen', required=False)
    genero = forms.ModelChoiceField(queryset=Genero.objects.all(), required=False)
    tel_pers = forms.CharField(label='Teléfono Personal', max_length=15, required=False)
    name_emerg = forms.CharField(label='Nombre de Emergencia', max_length=100, required=False)
    tel_emerg = forms.CharField(label='Teléfono de Emergencia', max_length=15, required=False)

    f_contratacion = forms.DateField(label='Fecha de Contratación', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    new_password1 = forms.CharField(label='Nueva contraseña', widget=forms.PasswordInput, required=False)
    new_password2 = forms.CharField(label='Confirmar nueva contraseña', widget=forms.PasswordInput, required=False)

    class Meta:
        model = JefePlataforma
        fields = [ 'f_contratacion']

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        jefe_plataforma = super().save(commit=False)
        user = jefe_plataforma.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.dni = self.cleaned_data['dni']
        user.f_nacim = self.cleaned_data['f_nacim']
        user.imagen = self.cleaned_data['imagen']
        user.genero = self.cleaned_data['genero']
        user.tel_pers = self.cleaned_data['tel_pers']
        user.name_emerg = self.cleaned_data['name_emerg']
        user.tel_emerg = self.cleaned_data['tel_emerg']
        if self.cleaned_data['new_password1']:
            user.set_password(self.cleaned_data['new_password1'])
        if commit:
            user.save()
            jefe_plataforma.save()
        return jefe_plataforma


class RecepcionistaProfileForm(forms.ModelForm):
    # username = forms.CharField(label='Nombre de usuario', max_length=150)
    first_name = forms.CharField(label='Nombre', max_length=150)
    last_name = forms.CharField(label='Apellido', max_length=150)
    dni = forms.CharField(label='DNI', max_length=12, required=False)
    f_nacim = forms.DateField(label='Fecha de Nacimiento', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    imagen = forms.ImageField(label='Imagen', required=False)
    genero = forms.ModelChoiceField(queryset=Genero.objects.all(), required=False)
    tel_pers = forms.CharField(label='Teléfono Personal', max_length=15, required=False)
    name_emerg = forms.CharField(label='Nombre de Emergencia', max_length=100, required=False)
    tel_emerg = forms.CharField(label='Teléfono de Emergencia', max_length=15, required=False)

    f_contratacion = forms.DateField(label='Fecha de Contratación', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    new_password1 = forms.CharField(label='Nueva contraseña', widget=forms.PasswordInput, required=False)
    new_password2 = forms.CharField(label='Confirmar nueva contraseña', widget=forms.PasswordInput, required=False)

    class Meta:
        model = Recepcionista
        fields = [ 'f_contratacion']

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        recepcionista = super().save(commit=False)
        user = recepcionista.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.dni = self.cleaned_data['dni']
        user.f_nacim = self.cleaned_data['f_nacim']
        user.imagen = self.cleaned_data['imagen']
        user.genero = self.cleaned_data['genero']
        user.tel_pers = self.cleaned_data['tel_pers']
        user.name_emerg = self.cleaned_data['name_emerg']
        user.tel_emerg = self.cleaned_data['tel_emerg']
        if self.cleaned_data['new_password1']:
            user.set_password(self.cleaned_data['new_password1'])
        if commit:
            user.save()
            recepcionista.save()
        return recepcionista


class MedicoProfileForm(forms.ModelForm):
    # username = forms.CharField(label='Nombre de usuario', max_length=150)
    first_name = forms.CharField(label='Nombre', max_length=150)
    last_name = forms.CharField(label='Apellido', max_length=150)
    dni = forms.CharField(label='DNI', max_length=12, required=False)
    f_nacim = forms.DateField(label='Fecha de Nacimiento', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    imagen = forms.ImageField(label='Imagen', required=False)
    genero = forms.ModelChoiceField(queryset=Genero.objects.all(), required=False)
    tel_pers = forms.CharField(label='Teléfono Personal', max_length=15, required=False)
    name_emerg = forms.CharField(label='Nombre de Emergencia', max_length=100, required=False)
    tel_emerg = forms.CharField(label='Teléfono de Emergencia', max_length=15, required=False)

    f_contratacion = forms.DateField(label='Fecha de Contratación', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    especialidad = forms.ModelMultipleChoiceField(queryset=Especialidad.objects.all(), required=False)
    sists_salud = forms.ModelMultipleChoiceField(queryset=SistemaSalud.objects.all(), required=False)
    curriculum = forms.CharField(label='Curriculum', widget=forms.Textarea, required=False)
    new_password1 = forms.CharField(label='Nueva contraseña', widget=forms.PasswordInput, required=False)
    new_password2 = forms.CharField(label='Confirmar nueva contraseña', widget=forms.PasswordInput, required=False)

    class Meta:
        model = Medico
        fields = [ 'dni', 'f_nacim', 'imagen', 'genero', 'tel_pers', 'name_emerg', 'tel_emerg','f_contratacion', 'especialidad', 'sists_salud', 'curriculum']

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        medico = super().save(commit=False)
        user = medico.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.dni = self.cleaned_data['dni']
        user.f_nacim = self.cleaned_data['f_nacim']
        user.imagen = self.cleaned_data['imagen']
        user.genero = self.cleaned_data['genero']
        user.tel_pers = self.cleaned_data['tel_pers']
        user.name_emerg = self.cleaned_data['name_emerg']
        user.tel_emerg = self.cleaned_data['tel_emerg']
        if self.cleaned_data['new_password1']:
            user.set_password(self.cleaned_data['new_password1'])
        if commit:
            user.save()
            medico.save()
        return medico



# class CompletarPerfilPacienteForm(forms.ModelForm):
#     username = forms.CharField(
#         max_length=150,
#         label='Nombre de usuario',
#         required=True) #Campo para el username
#     nueva_clave1 = forms.CharField(
#         widget=forms.PasswordInput,
#         required=False,
#         label='Ingrese su nueva contraseña',
#         help_text="Ingrese una contraseña segura. Debe tener al menos 8 caracteres, mayúsculas, minúsculas y números.",
#     )
#     nueva_clave2 = forms.CharField(
#         widget=forms.PasswordInput,
#         required=False,
#         label='Repita su nueva contraseña'
#     )

#     class Meta:
#         model = Paciente
#         fields = ['first_name', 'last_name', 'dni', 'f_nacim', 'imagen', 'genero', 't_personal', 'name_emergencia', 't_emergencia', 'grupoSangre', 'enfermedades', 'cirugias', 'alergias', 'medics_actuales', 'sistema_salud']
#         widgets = {
#             'f_nacim': forms.DateInput(attrs={'type': 'date'}),
#             'grupoSangre': forms.Select(choices=Paciente.gruposSangre), #Usa la tupla directamente del modelo
#             'sistema_salud': forms.Select(),
#             'genero': forms.Select(),
#         }




# class JefePlataformaSignupForm(forms.ModelForm):
#     f_contratacion = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Fecha de Contratación')
#     class Meta:
#         model   = JefePlataforma
#         fields  = ['username', 'email', 'f_contratacion']

# class CompletarPerfilJefePlataformaForm(forms.ModelForm):
#     nueva_clave  = forms.CharField(widget=forms.PasswordInput, required=True, label='Nueva Contraseña')
#     nueva_clave2 = forms.CharField(widget=forms.PasswordInput, required=True, label='Confirmar Nueva Contraseña')
#     f_nacim      = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Fecha de Nacimiento')

#     class Meta:
#         model = JefePlataforma
#         fields = [ 'username','dni','first_name', 'last_name','f_nacim', 'imagen', 'genero', 'tel_pers', 'name_emerg', 'tel_emerg']

#     def clean(self):
#         cleaned_data = super().clean()
#         nueva_clave = cleaned_data.get('nueva_clave')
#         nueva_clave2 = cleaned_data.get('nueva_clave2')

#         if nueva_clave and nueva_clave != nueva_clave2:
#             raise forms.ValidationError("Las contraseñas no coinciden.")
#         return cleaned_data

#     def save(self, commit=True):
#         jefe = super(CompletarPerfilJefePlataformaForm, self).save(commit=False)
#         nueva_clave = self.cleaned_data.get('nueva_clave')
#         if nueva_clave:
#             jefe.set_password(nueva_clave)
#         jefe.perfil_completo = True
#         if commit:
#             jefe.save()
#         return jefe


# #* ########################################
# #* #####  FORM PARA Recepcionista     #####
# #* ########################################
# class RecepcionistaSignupForm(forms.ModelForm):
#     class Meta:
#         model = Recepcionista
#         fields = 'username', 'email', 'f_contratacion'
#         widgets = {'f_contratacion': forms.DateInput(attrs={'type': 'date'}), }


# #* ########################################
# #* #####     FORM PARA MEDICOS        #####
# #* ########################################
# class MedicoSignupForm(forms.ModelForm):
#     class Meta:
#         model = Medico
#         fields = '__all__'
#         widgets = {
#                 'f_nacim': forms.DateInput(attrs={'type': 'date'}),
#                 'f_contratacion': forms.DateInput(attrs={'type': 'date'}),
#                 }




class GeneroForm(forms.ModelForm):
    class Meta:
        model = Genero
        fields = '__all__'

class EspecialidadForm(forms.ModelForm):
    class Meta:
        model = Especialidad
        fields = '__all__'

class SistemaSaludForm(forms.ModelForm):
    class Meta:
        model = SistemaSalud
        fields = '__all__'

class ExamenForm(forms.ModelForm):
    class Meta:
        model = Examen
        fields = '__all__'

class MedicamentoForm(forms.ModelForm):
    class Meta:
        model = Medicamento
        fields = '__all__'



# class RegistroJefePlataformaForm(forms.ModelForm):
#     class Meta:
#         model = JefePlataforma
#         fields = '__all__'
#         widgets = {
#                 'f_nacim': forms.DateInput(attrs={'type': 'date'}),
#                 'f_contratacion': forms.DateInput(attrs={'type': 'date'}),
#                 }

# class RegistroRecepcionistaForm(forms.ModelForm):
#     class Meta:
#         model = Recepcionista
#         fields = '__all__'
#         widgets = {
#                 'f_nacim': forms.DateInput(attrs={'type': 'date'}),
#                 'f_contratacion': forms.DateInput(attrs={'type': 'date'}),
#                 }

# class RegistroMedicoForm(forms.ModelForm):
#     class Meta:
#         model = Medico
#         fields = '__all__'
#         widgets = {
#                 'f_nacim': forms.DateInput(attrs={'type': 'date'}),
#                 'f_contratacion': forms.DateInput(attrs={'type': 'date'}),
#                 }





