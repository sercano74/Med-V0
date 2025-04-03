from django.urls import path
from .views import *
# from django.views.generic import LogoutView

app_name = 'A10_Usu'

urlpatterns = [
    path('', home, name='home'),
    path('registro_paciente/', registro_paciente, name='registro_paciente'),
    path('mensaje_verificacion_enviado/', mensaje_verificacion_enviado, name='mensaje_verificacion_enviado'),
    path('verificar_cuenta/<str:uidb64>/<str:token>/', verificar_cuenta, name='verificar_cuenta'),
    path('completar_perfil_paciente/<int:paciente_id>/', completar_perfil_paciente, name='completar_perfil_paciente'),
    path('listar_pacientes/', listar_pacientes, name='listar_pacientes'),

    path('usuarios/', usuarios, name='usuarios'),
    path('registro_usuario/', registro_usuario, name='registro_usuario'),
    path('completar_perfil_jefe_plataforma/<int:jefe_plataforma_id>/', completar_perfil_jefe_plataforma, name='completar_perfil_jefe_plataforma'),
    path('completar_perfil_recepcionista/<int:recepcionista_id>/', completar_perfil_recepcionista, name='completar_perfil_recepcionista'),
    path('completar_perfil_medico/<int:medico_id>/', completar_perfil_medico, name='completar_perfil_medico'),
    path('ver_perfilout/<int:user_id>/', ver_perfilout, name='ver_perfilout'),
    # path('registro_jefe_plataforma/', registro_jefe_plataforma, name='registro_jefe_plataforma'),
    # path('registro_recepcionista/', registro_recepcionista, name='registro_recepcionista'),

    path('cambiar_rol/',cambiar_rol,name='cambiar_rol'),

    path('vista_parametros/', vista_parametros, name='vista_parametros'),
    path('registro_genero/', registro_genero, name='registro_genero'),
    path('registro_especialidad', registro_especialidad, name='registro_especialidad'),
    path('registro_sistema_salud/', registro_sistema_salud, name='registro_sistema_salud'),
    path('registroExamen/', registroExamen, name='registroExamen'),
    path('registroMedicamento/', registroMedicamento, name='registroMedicamento'),
    path('medicamento/<int:pk>/', medicamentoVer, name='medicamentoVer'),
    path('medicamento/editar/<int:pk>/', medicamentoEditar, name='medicamentoEditar'),

]

