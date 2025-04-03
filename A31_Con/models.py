from django.db import models
from A20_Hrs.models import *

# Create your models here.
class Examen(models.Model):
    nombre          = models.CharField(max_length=100)
    descripcion     = models.TextField(blank=True, null=True)
    class Meta:
        verbose_name = 'Examen'
        verbose_name_plural = 'Examenes'
        ordering     = ['nombre']
    def __str__(self):
        return f'{self.nombre}'

#* Abajo hay una tabla con ejemplos de examenes

class Medicamento(models.Model):
    nombre_gen      = models.CharField(max_length=100,help_text='Nombre genérico')
    nombre_com      = models.CharField(max_length=100,help_text='Nombre comercial')
    laboratorio     = models.CharField(max_length=100,help_text='Laboratorio',blank=True, null=True)
    forma_farma     = models.CharField(max_length=100,help_text='Forma farmacéutica')
    presentacion    = models.CharField(max_length=100,help_text='Presentación')
    descripcion     = models.TextField(blank=True, null=True, help_text='Descripción')
    archivo         = models.FileField(upload_to="Medicamentos", max_length=100, blank=True, null=True,help_text='Ficha técnica')
    estado          = models.CharField(max_length=20, choices=[('activo','Activo'),('inactivo', 'Inactivo')], default='activo')
    class Meta:
        verbose_name = 'Medicamento'
        verbose_name_plural = 'Medicamentos'
        ordering    = ['nombre_gen']
    def __str__(self):
        return f'{self.nombre_gen}'

class Consulta(models.Model):
    hora_medica     = models.ForeignKey(HoraMedica, on_delete=models.CASCADE, related_name='hora_medica_consultas')
    temperatura     = models.FloatField()
    p_sistolica     = models.IntegerField()
    p_diastolica    = models.IntegerField()
    altura          = models.FloatField(default=0.0)
    peso            = models.FloatField(default=0.0)
    imc             = models.FloatField(blank=True, null=True, default=0.0)
    notas           = models.TextField(blank=True, null=True)
    sintomas        = models.TextField(blank=True, null=True, default='Sin síntomas')
    diagnostico     = models.TextField()
    estado          = models.CharField(max_length=20, choices=[('NoIniciada','No Iniciada'),('Iniciada', 'Iniciada'), ('Finalizada', 'Finalizada')], default='NoIniciada')
    observaciones   = models.TextField(blank=True, null=True, default='Sin observaciones', help_text="Observaciones o instrucciones adicionales para el paciente sobre los exámenes.")
    had_OrdExams    = models.BooleanField(default=False, help_text="¿Se han solicitado exámenes?")
    had_Receta      = models.BooleanField(default=False, help_text="¿Se ha recetado algún medicamento?")
    had_Certificado = models.BooleanField(default=False, help_text="¿Se ha emitido algún certificado?")
    resultados_enviados = models.BooleanField(default=False, help_text="¿Se han enviado los resultados al médico?")
    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        ordering = ['hora_medica']
    def __str__(self):
        return f'Consulta {self.id} [{self.hora_medica}-{self.estado}]'


class Consulta_Doc(models.Model):
    consulta        = models.ForeignKey(Consulta, on_delete=models.CASCADE, related_name='consulta_docs')
    doc_exam        = models.FileField(upload_to='Docs_Exams/', blank=True, null=True)
    notas_exams     = models.TextField(blank=True, null=True)
    class Meta:
        verbose_name = 'Resultado de exámen'
        verbose_name_plural = 'Resultado de Exámenes'
        ordering = ['consulta']
    def __str__(self):
        return f'Resultado de Exámen {self.id} [Consulta {self.consulta}]'


class Consulta_Examen(models.Model):
    consulta        = models.ForeignKey(Consulta, on_delete=models.CASCADE, related_name='consulta_examenes')
    examen          = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name='examen_consultas')
    resultado       = models.TextField(blank=True, null=True)
    archivo         = models.FileField(upload_to="Examenes", max_length=100)
    estado          = models.CharField(max_length=20, choices=[('solicitado','Solicitado'),('subido', 'Subido'), ('anulado', 'Anulado')], default='solicitado')
    class Meta:
        verbose_name = 'Consulta Examen'
        verbose_name_plural = 'Consultas Examenes'
        ordering = ['consulta']
    def __str__(self):
        return f'Consulta Examen {self.id} [{self.consulta}/{self.examen}]'

class Consulta_Receta(models.Model):
    consulta        = models.ForeignKey(Consulta, on_delete=models.CASCADE, related_name='consulta_recetas')
    medicamento     = models.ForeignKey(Medicamento, on_delete=models.CASCADE, related_name='medicamento_consultas')
    via             = models.CharField(max_length=100,help_text='Vía de administración')
    dosis           = models.CharField(max_length=100,help_text='Dosis a administrar')
    frecuencia      = models.CharField(max_length=100,help_text='Frecuencia de administración')
    duracion        = models.CharField(max_length=100,help_text='Duración del tratamiento')
    class Meta:
        verbose_name = 'Consulta Receta'
        verbose_name_plural = 'Consultas Recetas'
        ordering = ['consulta']
    def __str__(self):
        return f'Consulta Receta {self.id} [{self.consulta}/{self.medicamento}]'


class Consulta_Certificado(models.Model):
    consulta        = models.ForeignKey(Consulta, on_delete=models.CASCADE, related_name='consulta_certificados')
    fecha_emision   = models.DateField(auto_now_add=True)
    lugar_emision   = models.CharField(blank=True, null=True,max_length=100,help_text='Lugar de emisión')
    dirigido_a      = models.CharField(blank=True, null=True,max_length=100,help_text='Dirigido a')
    email_empleador = models.EmailField(blank=True, null=True)
    antecedentes    = models.TextField(blank=True, null=True,help_text='Antecedentes clínicos')
    diagnosis       = models.TextField(blank=True, null=True,help_text='Diagnóstico')
    recomendaciones = models.TextField(blank=True, null=True,help_text='Recomendaciones')
    inicio          = models.DateField(blank=True, null=True)
    termino         = models.DateField(blank=True, null=True)
    archivo         = models.FileField(blank=True, null=True,upload_to="Certificados", max_length=100)
    class Meta:
        verbose_name = 'Consulta Certificado'
        verbose_name_plural = 'Consultas Certificados'
        ordering = ['consulta']
    def __str__(self):
        return f'Certificado {self.id} [Consulta {self.consulta}]'


class Consulta_imagen(models.Model):
    consulta        = models.ForeignKey(Consulta, on_delete=models.CASCADE, related_name='consulta_imagenes')
    imagen          = models.ImageField(upload_to='images/', blank=True, null=True)
    diagnostico     = models.TextField(blank=True, null=True)
    class Meta:
        verbose_name = 'Consulta Imagen'
        verbose_name_plural = 'Consultas Imagenes'
        ordering = ['consulta']
    def __str__(self):
        return f'Consulta Imagen {self.id} [{self.consulta}/{self.imagen}]'




#* Ejemplos de examenes
#   Examen Médico	                    Descripción
# Hemograma Completo	        Analiza la cantidad y tipo de células sanguíneas (glóbulos rojos, glóbulos blancos, plaquetas). Útil para detectar anemias, infecciones y trastornos de la coagulación.
# Perfil Lipídico	            Mide los niveles de colesterol y triglicéridos en la sangre. Ayuda a evaluar el riesgo de enfermedades cardiovasculares.
# Glucemia en Ayunas	        Mide el nivel de glucosa en la sangre después de un período de ayuno. Se utiliza para diagnosticar diabetes o resistencia a la insulina.
# Urianálisis	                Examina las características físicas, químicas y microscópicas de la orina. Puede revelar infecciones urinarias, enfermedades renales o diabetes.
# Electrocardiograma (ECG)	    Registra la actividad eléctrica del corazón. Se utiliza para detectar arritmias, enfermedades cardíacas o daño al músculo cardíaco.