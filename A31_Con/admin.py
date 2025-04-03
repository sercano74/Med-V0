from django.contrib import admin
from django.contrib.auth.models import User
from .models import *

# Register your models here.
admin.site.register(Examen)
admin.site.register(Medicamento)
admin.site.register(Consulta)
admin.site.register(Consulta_Examen)
admin.site.register(Consulta_Receta)
admin.site.register(Consulta_imagen)
admin.site.register(Consulta_Certificado)
admin.site.register(Consulta_Doc)
