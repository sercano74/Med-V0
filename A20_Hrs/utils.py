from django.utils import timezone
from .models import HoraMedica

def actualizar_horas_anular():
    ahora = timezone.now()
    horas_pasadas_libres_tomadas = HoraMedica.objects.filter(f_hra__lt=ahora, estado='libre')|HoraMedica.objects.filter(f_hra__lt=ahora, estado='tomada')
    horas_pasadas_libres_tomadas.update(estado='anulada')

    horas_pasadas_pagadas = HoraMedica.objects.filter(f_hra__lt=ahora, estado='pagada')
    horas_pasadas_pagadas.update(estado='perdida')

