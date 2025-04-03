from django.db import models
from A10_Usu.models import *

class FichaMedica(models.Model):
    paciente        = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='paciente_fichas')
    medico          = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='medico_fichas')
    f_consulta      = models.DateTimeField(auto_now_add=True)
    temperatura     = models.FloatField()
    p_sistolica     = models.IntegerField()
    p_diastolica    = models.IntegerField()
    altura          = models.FloatField(default=0.0)
    peso            = models.FloatField(default=0.0)
    imc             = models.FloatField(blank=True, null=True, default=0.0)
    sintomas        = models.TextField(blank=True, null=True, default='Sin síntomas')
    diagnostico     = models.TextField()
    prescripcion    = models.TextField()
    notas           = models.TextField(blank=True, null=True)
    estado          = models.CharField(max_length=20, choices=[('NoIniciada','No Iniciada'),('Abierta', 'Abierta'), ('Cerrada', 'Cerrada')], default='NoIniciada')

    class Meta:
        verbose_name        = 'Ficha Médica'
        verbose_name_plural = 'Fichas Médicas'
        ordering            = ["f_consulta","estado"]

    def __str__(self):
        return f'Ficha Médica {self.id} [{self.f_consulta}/{self.estado}] [{self.medico}/{self.paciente}]'

    # def imc(self):
    #     if self.altura and self.peso:
    #         return round(self.peso/(self.altura**2),2)
    #     return None


