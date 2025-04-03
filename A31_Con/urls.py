from django.urls import path
from .views import *
# from django.views.generic import LogoutView

app_name = 'A31_Con'

urlpatterns = [
    path('consultas_ajax/', consultas_ajax, name='consultas_ajax'),
    path('consultas/', consultas, name='consultas'),
    path('consulta_iniciar/<int:hora_id>/', consulta_iniciar, name='consulta_iniciar'),
    path('consulta_detalle/<int:consulta_id>/', consulta_detalle, name='consulta_detalle'),
    path('enviar_resultados_al_medico/<int:consulta_id>/', enviar_resultados_al_medico, name='enviar_resultados_al_medico'),
    path('consulta_editar/<int:consulta_id>/', consulta_editar, name='consulta_editar'),

    path('examen/<int:examen_id>/subir/', subir_resultado_examen, name='subir_resultado_examen'),
    path('examen/<int:examen_id>/bajar/', bajar_resultado_examen, name='bajar_resultado_examen'),

    path('obtener_medicamentos_seleccionados/', obtener_medicamentos_seleccionados, name='obtener_medicamentos_seleccionados'),
    path('imprimir_orden_examen/<int:consulta_id>/', imprimir_orden_examen, name='imprimir_orden_examen'),
    path('imprimir_prescripcion/<int:consulta_id>/', imprimir_prescripcion, name='imprimir_prescripcion'),
    path('imprimir_certificado/<int:consulta_id>/', imprimir_certificado, name='imprimir_certificado'),
    path('enviar_email_certificado/<int:consulta_id>/', enviar_email_certificado, name='enviar_email_certificado'),


    path('consulta_informes/', consulta_informes, name='consulta_informes'),
    path('informe_historico/<int:paciente_id>/',informe_historico, name='informe_historico'),
    path('consultas_resumen/<int:paciente_id>/',consultas_resumen, name='consultas_resumen'),


]
