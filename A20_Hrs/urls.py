from django.urls import path
from .views import *
# from django.views.generic import LogoutView

app_name = 'A20_Hrs'

urlpatterns = [
    path('listar_horas_medicas/', listar_horas_medicas, name='listar_horas_medicas'),
    path('crear_hora_medica/', crear_hora_medica, name='crear_hora_medica'),
    path('registro_hora_medica/', registro_hora_medica, name='registro_hora_medica'),
    # path('editar/<int:hora_medica_id>/', editar_hora_medica, name='editar_hora_medica'),
    # path('eliminar/<int:hora_medica_id>/', eliminar_hora_medica, name='eliminar_hora_medica'),

    path('seleccionar_paciente/', seleccionar_paciente, name='seleccionar_paciente'),
    # path('solicitar_horapara/<int:paciente_id>/', solicitar_horapara, name='solicitar_horapara'),
    # path('gestionar_hora/<int:paciente_id>/', gestionar_hora, name='gestionar_hora_para'),

    path('solicitar/', solicitar_hora, name='solicitar_hora'),
    path('gestionar_hora/', gestionar_hora, name='gestionar_hora'),

    path('liberar_hora/', liberar_hora, name='liberar_hora'),
    path('liberar_hora/<int:paciente_id>/', liberar_hora, name='liberar_hora_para'),

    path('ver_horas_paciente/', ver_horas_paciente, name='ver_horas_paciente'),
    path('ver_horas_paciente/<int:paciente_id>/', ver_horas_paciente, name='ver_horas_paciente_para'),

    path('calendario_horasmedicas/', calendario_horasmedicas, name='calendario_horasmedicas'),
    path('horasmedicas_x_dia/<int:year>/<int:month>/<int:day>/', horasmedicas_x_dia, name='horasmedicas_x_dia'),
    path('calendario_medico/', calendario_medico, name='calendario_medico'),
    path('ver_horasmedico/<int:medico_id>/<str:fecha>/', ver_horasmedico, name='ver_horasmedico'),
    path('editar_hora_medica/<int:hora_medica_id>/', editar_hora_medica, name='editar_hora_medica'),
    path('eliminar_hora_medica/<int:hora_medica_id>/', eliminar_hora_medica, name='eliminar_hora_medica'),
    path('solicitar_horapara_desdehora/<int:hora_medica_id>/', solicitar_horapara_desdehora, name='solicitar_horapara_desdehora'),
    path('solicitar_horapara/<int:user_id>',solicitar_horapara, name="solicitar_horapara"),

    path('registrar_pago_efectivo/<int:hora_medica_id>/', registrar_pago_efectivo, name='registrar_pago_efectivo'),
    path('registrar_pago_bono/<int:hora_medica_id>/', registrar_pago_bono, name='registrar_pago_bono'),
    path('registrar_pago_tarjeta/<int:hora_medica_id>/', registrar_pago_tarjeta, name='registrar_pago_tarjeta'),

    path('vistaInfAdm/', vistaInfAdm, name='vistaInfAdm'),
    path('informe_diario_horas_medicas/', informe_diario_horas_medicas, name='informe_diario_horas_medicas'),
    path('informe_mensual_horas_medicas/', informe_mensual_horas_medicas, name='informe_mensual_horas_medicas'),

]