from django.urls import path
from .views import *
# from django.views.generic import LogoutView

app_name = 'A30_Fic'

urlpatterns = [

    path('listar_pacientes_con_horas/', listar_pacientes_con_horas, name='listar_pacientes_con_horas'),
    path('iniciar_ficha_medica/<int:paciente_id>/', iniciar_ficha_medica, name='iniciar_ficha_medica'),
    path('iniciar_ficha_hora/<int:hora_id>/', iniciar_ficha_hora, name='iniciar_ficha_hora'),
    path('listar_fichas_medicas_ajax/', listar_fichas_medicas_ajax, name='listar_fichas_medicas_ajax'),
    path('listar_fichas_medicas/', listar_fichas_medicas, name='listar_fichas_medicas'),
    path('listar_mis_fichas_medicas/', listar_mis_fichas_medicas, name='listar_mis_fichas_medicas'),
    path('ver_ficha_medica/<int:ficha_id>/', ver_ficha_medica, name='ver_ficha_medica'),
    path('modificar_ficha_medica/<int:ficha_id>/', modificar_ficha_medica, name='modificar_ficha_medica'),
    path('reasignar_ficha_medica/<int:ficha_id>/', reasignar_ficha_medica, name='reasignar_ficha_medica'),
    path('historial_medico/<int:paciente_id>/', historial_medico, name='historial_medico'),
]