from django.contrib import admin
from django.contrib.auth.models import User
from .models import *

admin.site.register(HoraMedica)
admin.site.register(Pago)
# Register your models here.