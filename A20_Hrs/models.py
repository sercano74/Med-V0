from django.db import models
from A10_Usu.models import *

class HoraMedica(models.Model):
    medico      = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name ='medico_horas')
    f_hra       = models.DateTimeField()
    costo       = models.DecimalField(max_digits=10, decimal_places=2)
    paciente    = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name ='paciente_horas', null=True, blank=True)
    pagada      = models.BooleanField(default=False)
    estado      = models.CharField(max_length=20, choices=[('libre','Libre'),('tomada','Tomada'),('pagada','Pagada'),('iniciada','Iniciada'),('anulada','Anulada'),('perdida','Perdida'),], default='libre')
    class Meta:
        verbose_name        = 'Hora Médica'
        verbose_name_plural = 'Horas Médicas'
        ordering            = ["f_hra"]
    def __str__(self):
        return f'Hora Médica {self.id} [{self.f_hra}/{self.get_estado_display()}] [{self.medico}/{self.paciente}]'
    def clean(self): #Validacion para que no se creen horas medicas en el pasado
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        if self.f_hra < timezone.now():
            raise ValidationError('No se pueden crear horas médicas en el pasado.')

    def save(self, *args, **kwargs):
        self.full_clean() #Llamar al clean para que se ejecute la validacion
        super().save(*args, **kwargs)


class Pago(models.Model):
    hora_medica     = models.OneToOneField(HoraMedica, on_delete=models.CASCADE, related_name='pago')
    fecha_pago      = models.DateTimeField(auto_now_add=True)
    tipo_pago       = models.CharField(max_length=20, choices=[('efectivo', 'Efectivo'), ('tarjeta','Tarjeta Crédito'),('bono', 'Bono Isapre')])
    monto           = models.DecimalField(max_digits=10, decimal_places=2)
    sistema_salud   = models.ForeignKey(SistemaSalud, on_delete=models.SET_NULL, null=True, blank=True)  # Para pagos con bono
    numero_bono     = models.CharField(max_length=20, blank=True, null=True)  # Para pagos
    numero_tarjeta  = models.CharField(max_length=20, blank=True, null=True)  # Para pagos con tarjeta de crédito
    numero_transaccion = models.CharField(max_length=20, blank=True, null=True)  # Para pagos con tarjeta de crédito
    # ... otros campos si es necesario (ej: número de transacción, etc.)

    def __str__(self):
        return f"Pago para la hora médica {self.hora_medica.id} el {self.fecha_pago}"