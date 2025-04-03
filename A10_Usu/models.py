from datetime import date
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models


class Genero(models.Model):
    name    = models.CharField(max_length=15,null=True, blank=True, unique=True)
    class Meta:
        verbose_name = 'Género'
        verbose_name_plural = 'Géneros'
        ordering = ['name']
    def __str__(self):
        return f'{self.name}'

class SistemaSalud(models.Model):
    name    = models.CharField(max_length=100,null=True, blank=True, unique=True)
    class Meta:
        verbose_name = 'Sistema de Salud'
        verbose_name_plural = 'Sistemas de Salud'
        ordering = ['name']
    def __str__(self):
        return f'{self.name}'

class Especialidad(models.Model):
    name    = models.CharField(max_length=25,null=True, blank=True, unique=True)
    class Meta:
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'
        ordering = ['name']
    def __str__(self):
        return f'{self.name}'


class CustomUser(AbstractUser):
    username    = models.CharField(max_length=150, unique=False, null=True, blank=True)
    email       = models.EmailField(unique=True)
    dni         = models.CharField(max_length=12, unique=True, null=True, blank=True)
    f_nacim     = models.DateField(null=True, blank=True)
    imagen      = models.ImageField(upload_to='images/', blank=True, null=True)
    genero      = models.ForeignKey(Genero, on_delete=models.RESTRICT,null=True, blank=True)
    tel_pers    = models.CharField(max_length=15, blank=True, null=True)
    name_emerg  = models.CharField(max_length=100, blank=True, null=True)
    tel_emerg   = models.CharField(max_length=15, blank=True, null=True)
    created     = models.DateTimeField(auto_now_add=True)
    updated     = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f'U: {self.email}'


class JefePlataforma(models.Model):
    user            = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='jefeplataforma_profile')
    f_contratacion  = models.DateField(null=True, blank=True)
    perfil_completo = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Jefe de Plataforma'
        verbose_name_plural = 'Jefes de Plataforma'
        permissions         = (("Home_JefePlataforma","Home Jefe de Plataforma"),)
        # ordering            = ["-created","dni"]

    def __str__(self):
        return f'J-P.  {self.user.first_name} {self.user.last_name}'


class Recepcionista(models.Model):
    user            = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='recepcionista_profile')
    f_contratacion  = models.DateField(null=True, blank=True)
    perfil_completo = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Recepcionista'
        verbose_name_plural = 'Recepcionistas'
        permissions         = (("Home_Recepcionista","Home Recepcionista"),)
        # ordering            = ["-id",-created","dni"]

    def __str__(self):
        return f'Recep. {self.user.first_name} {self.user.last_name}'


class Medico(models.Model):
    user            = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='medico_profile')
    especialidad    = models.ManyToManyField(Especialidad,  blank=True)
    sists_salud     = models.ManyToManyField(SistemaSalud,  blank=True)
    curriculum      = models.TextField(blank=True, null=True)
    f_contratacion  = models.DateField(null=True, blank=True)
    perfil_completo = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Medico'
        verbose_name_plural = 'Medicos'
        permissions         = (("Home_Medico","Home Medico"),)
        # ordering            = ["-BaseUser.created","BaseUser.dni"]

    def __str__(self):
        return f'Dc. {self.user.first_name} {self.user.last_name}'


    # user            = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='paciente_profile', default=None)
    #* related_name: Este argumento permite definir un nombre personalizado para el accessor inverso. Por ejemplo, en este caso, puedes acceder al objeto Paciente asociado a un CustomUser a través de customuser_ptr.paciente_profile o user.paciente_profile, indistintamente.

class Paciente(models.Model):
    user            = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='paciente_profile')
    gruposSangre    = (('1','0-'),('2','0+'),('3','A-'),('4','A+'),('5','B-'),('6','B+'),('7','AB-'),('8','AB+'),('9','Otro'))
    grupoSangre     = models.CharField(choices= gruposSangre, max_length=4,null=True, blank=True)
    enfermedades    = models.TextField(blank=True, null=True)
    cirugias        = models.TextField(blank=True, null=True)
    alergias        = models.TextField(blank=True, null=True)
    meds_actuales   = models.TextField(blank=True, null=True)
    sistema_salud   = models.ForeignKey('SistemaSalud', on_delete=models.RESTRICT,null=True, blank=True)
    perfil_completo = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Paciente'
        verbose_name_plural = 'Pacientes'
        permissions         = (("Home_Paciente","Home Paciente"),)
        # ordering            = ["-BaseUser.created","BaseUser.dni"]
    @property
    def is_paciente(self):
        return hasattr(self, 'paciente_profile')
    def __str__(self):
        return f'Pacte. {self.user.first_name} {self.user.last_name}'




    # def calcular_edad(self):
    #     hoy = date.today()
    #     edad = hoy.year - self.f_nacim.year - ((hoy.month, hoy.day) < (self.f_nacim.month, self.f_nacim.day))
    #     return edad

    # def cumple_hoy(self):
    #     hoy = date.today()
    #     if hoy.month == self.f_nacim.month and  hoy.day == self.f_nacim.day:
    #         cumple = True
    #         #TODO send email
    #     else:
    #         cumple = False
    #         return cumple