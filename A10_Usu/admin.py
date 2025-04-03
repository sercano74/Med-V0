from django.contrib import admin
from django.contrib.auth.models import User
from .models import *

# ASIGNAMOS ROTULOS PARA EL CONTROL PANEL Y MÁS
admin.site.index_title  = 'Med'
admin.site.site_title   = 'Panel De Control'
admin.site.site_header  = 'PLATAFORMA PARA LA GESTIÓN DE CENTROS MÉDICOS'

# Register your models here.
admin.site.register(SistemaSalud)
admin.site.register(Genero)
admin.site.register(Especialidad)

admin.site.register(CustomUser)
admin.site.register(JefePlataforma)
admin.site.register(Recepcionista)
admin.site.register(Medico)
admin.site.register(Paciente)