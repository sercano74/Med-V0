from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from A10_Usu.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name="home.html"), name='home'),

    path('accounts/', include('allauth.urls')),

    # path('accounts/signup/paciente/', registro_paciente, name='registro_paciente'),
    # path('accounts/signup/registro_jefe_plataforma/',registro_jefe_plataforma, name='registro_jefe_plataforma'),

    path('accounts/redireccion_despues_login/', redireccion_despues_login, name='redireccion_despues_login'),
    path('accounts/seleccionar_tipo_registro/', seleccionar_tipo_registro, name='seleccionar_tipo_registro'),

    path('accounts/completar_perfil_paciente/', completar_perfil_paciente, name='completar_perfil_paciente'),
    # path('accounts/email-confirmation/<key>/', CustomConfirmEmailView.as_view(), name='account_confirm_email'),
    # path('accounts/completar_perfil_jefe_plataforma/', completar_perfil_jefe_plataforma, name='completar_perfil_jefe_plataforma'),


    # path('accounts/signup/recepcionista/', registro_recepcionista, name='registro_recepcionista'),
    # path('accounts/signup/medico/', registro_medico, name='registro_medico'),
    path('gestion_usuarios/', include('A10_Usu.urls', namespace='Usuarios')),
    path('horas_medicas/', include('A20_Hrs.urls', namespace='Horas Medicas')),
    path('fichas_medicas/', include('A30_Fic.urls',namespace='Fichas Medicas')),
    path('consultas/', include('A31_Con.urls',namespace='Consultas')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

