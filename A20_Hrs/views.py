from .forms import *
from .models import *
from .utils import actualizar_horas_anular
from A10_Usu.models import *
from babel.dates import format_date
from collections import defaultdict
from datetime import datetime,timedelta
from datetime import datetime, date
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib.auth import login
from django.core.mail import send_mail
from django.db import transaction, OperationalError
from django.http import Http404, HttpResponse, JsonResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.formats import dateformat
from django.utils import timezone
from fpdf import FPDF
from icecream import ic

import calendar
import locale
import os
ahora = timezone.now()

@login_required #Ok
def listar_horas_medicas(request):
    if not request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() and not request.user.is_superuser:
        messages.error(request,"No tienes permisos para realizar esta acción")
        return redirect('home')

    horas_medicas = HoraMedica.objects.all()

    if request.method == 'POST':
        form = EditarHoraMedicaForm(request.POST)
        if form.is_valid():
            hora_medica_id = request.POST.get('hora_medica_id') #Obtener el id de la hora medica
            hora_medica = get_object_or_404(HoraMedica, pk=hora_medica_id)
            hora_medica.medico = form.cleaned_data['medico']
            hora_medica.costo = form.cleaned_data['costo']
            hora_medica.f_hra = form.cleaned_data['f_hra']
            hora_medica.paciente = form.cleaned_data['paciente']
            hora_medica.estado = form.cleaned_data['estado']
            hora_medica.save()
            messages.success(request, "Hora médica actualizada correctamente.")
            return redirect('Horas Medicas:listar_horas_medicas')  # Redirige a la misma página
        else:
            messages.error(request, "Error al actualizar la hora médica. Revisa los datos.")

    context = {'horas_medicas': horas_medicas, 'form': EditarHoraMedicaForm(),'especialidades': Especialidad.objects.all()}
    return render(request, 'A20_Hrs/listar_horas_medicas.html', context)


@login_required #Ok
def crear_hora_medica(request):
    if not request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() and not request.user.is_superuser:
        messages.error(request,"No tienes permisos para realizar esta acción")
        return redirect('home')
    if request.method == 'POST':
        form = HoraMedicaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    hora_medica = form.save()
                    messages.success(request, 'Hora médica creada correctamente.')
                    return redirect('A20_Hrs:calendario_horasmedicas')
            except Exception as e:
                messages.error(request, f"Error al crear la hora médica: {e}")
        else:
            messages.error(request, "Por favor, corrige los errores en el formulario.")
    else:
        form = HoraMedicaForm()
    return render(request, 'A20_Hrs/crear_hora_medica.html', {'form': form})


@login_required #Ok
def seleccionar_paciente(request):
    if request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() or request.user.is_superuser:
        pacientes = Paciente.objects.all()
        return render(request, 'A20_Hrs/seleccionar_paciente.html', {'pacientes': pacientes})
    else:
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('home')


@login_required
def registro_hora_medica(request):
    if request.method == 'POST':
        form =  HoraMedicaForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form =  HoraMedicaForm()
    return render(request, 'A20_Hrs/registro_hora_medica.html', {'form': form})


@login_required
def editar_hora_medica(request, hora_medica_id):
    if not request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() and not request.user.is_superuser:
        messages.error(request,"No tienes permisos para realizar esta acción")
        return redirect('home')
    hora_medica = get_object_or_404(HoraMedica, pk=hora_medica_id)
    if request.method == 'POST':
        form = EditarHoraMedicaForm(request.POST, instance=hora_medica)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, 'Hora médica editada correctamente.')
                    return redirect('listar_horas_medicas')
            except Exception as e:
                messages.error(request, f"Error al editar la hora médica: {e}")
        else:
            messages.error(request, "Por favor, corrige los errores en el formulario.")
    else:
        form = EditarHoraMedicaForm(instance=hora_medica)
    return render(request, 'A20_Hrs/editar_hora_medica.html', {'form': form, 'hora_medica': hora_medica})


@login_required
def eliminar_hora_medica(request, hora_medica_id):
    if not request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() and not request.user.is_superuser:
        messages.error(request,"No tienes permisos para realizar esta acción")
        return redirect('home')
    hora_medica = get_object_or_404(HoraMedica, pk=hora_medica_id)
    try:
        hora_medica.delete()
        messages.success(request, 'Hora médica eliminada correctamente.')
    except Exception as e:
        messages.error(request, f"Error al eliminar la hora médica: {e}")
    return redirect('listar_horas_medicas')


@login_required
def solicitar_hora(request):
    try:
        paciente = get_object_or_404(Paciente, user=request.user)
        messages.success(request, "Tú perfil de paciente ha sido confirmado!")
    except Http404:
        messages.error(request, "Usted no posee credencial para solicitar hora por cuenta de un paciente. Sólo el paciente puede solicitar hora para sí mismo.")
        return redirect('home')

    # Limpiar las variables de sesión al inicio de la vista
    request.session.pop('esp', None) # Elimina la variable de sesión 'esp' si existe
    request.session.pop('med', None)

    especialidades  = Especialidad.objects.all()
    medicos         = Medico.objects.none() # Inicializar queryset vacío
    horas_medicas   = HoraMedica.objects.none()

    if request.method == 'POST':
        with transaction.atomic():
            hora_medica_id = request.POST.get('hora_medica')
            hora_medica = get_object_or_404(HoraMedica, id=hora_medica_id)
            hora_medica.paciente = paciente
            hora_medica.estado = 'tomada'
            hora_medica.save()

            messages.success(request, "Hora médica solicitada exitosamente.")
            return redirect('A20_Hrs:listar_horas_medicas')

    if 'esp' in request.GET and request.GET['esp']:
        try:
            request.session['esp'] = int(request.GET['esp'])
        except ValueError:
            request.session['esp'] = None

    if request.session.get('esp'):
        esp = request.session['esp']
        espSel = get_object_or_404(Especialidad, id=esp)
        medicos = Medico.objects.filter(
            especialidad=espSel,
            medico_horas__estado='libre',
            medico_horas__f_hra__gt=timezone.now()
        ).distinct()

        if not medicos.exists():
            messages.info(request, f"No hay médicos con horas disponibles para la especialidad {espSel.name}.")
        else:
            messages.success(request, f"Para la especialidad: {espSel.name}. Se han encontrado los siguientes médicos: {medicos}")

    if 'med' in request.GET and request.GET['med']:
        try:
            request.session['med'] = int(request.GET['med'])
        except ValueError:
            request.session['med'] = None

    if request.session.get('med'):
        med = request.session['med']
        medSel = get_object_or_404(Medico, user_id=med)
        horas_medicas = HoraMedica.objects.filter(
            medico=medSel,
            estado='libre',
            f_hra__gt=timezone.now()  # Solo horas futuras
        )

        if not horas_medicas.exists():
            messages.info(request, f"No hay horas médicas disponibles para el médico {medSel.user.first_name} {medSel.user.last_name}.")
        else:
            messages.success(request, f"Para el médico: {medSel.user.first_name} {medSel.user.last_name}. Se han encontrado las siguientes horas médicas: {horas_medicas}")

    return render(request, 'A20_Hrs/solicitar_hora.html', {
        'especialidades': especialidades,
        'medicos': medicos,
        'horas_medicas': horas_medicas,
        'esp': request.session.get('esp'),
        'med': request.session.get('med'),
    })



import logging
logger = logging.getLogger(__name__)

@login_required
def solicitar_horapara(request, user_id):
    user = get_object_or_404(CustomUser,pk=user_id)
    logger.debug(f"Usuario: {user.username}, Grupos: {user.groups.all()}") #Log agregado.
    if request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionistas']).exists() or request.user.is_superuser:

        #Limpiar las variables de sesión al inicio de la vista
        request.session.pop('esp', None)
        request.session.pop('med', None)

        especialidades = Especialidad.objects.all()
        medicos = Medico.objects.none()
        horas_medicas = HoraMedica.objects.none()

        if request.method == 'POST':
            try:
                paciente = user.paciente_profile

                with transaction.atomic():
                    hora_medica_id = request.POST.get('hora_medica')
                    hora_medica = get_object_or_404(HoraMedica, id=hora_medica_id)
                    hora_medica.paciente = paciente
                    hora_medica.estado = 'tomada'
                    hora_medica.save()

                    messages.success(request, "Hora médica solicitada exitosamente.")
                    return redirect('A20_Hrs:calendario_horasmedicas')
            except Paciente.DoesNotExist:
                messages.error(request, "El usuario no tiene un perfil de paciente.")
                return redirect('home')

        if 'esp' in request.GET and request.GET['esp']:
            try:
                request.session['esp'] = int(request.GET['esp'])
            except ValueError:
                request.session['esp'] = None

        if request.session.get('esp'):
            esp = request.session['esp']
            espSel = get_object_or_404(Especialidad, id=esp)
            medicos = Medico.objects.filter(
                especialidad=espSel,
                medico_horas__estado='libre',
                medico_horas__f_hra__gt=timezone.now()
            ).distinct()

            if not medicos.exists():
                messages.info(request, f"No hay médicos con horas disponibles para la especialidad {espSel.name}.")
            else:
                messages.success(request, f"Para la especialidad: {espSel.name}. Se han encontrado los siguientes médicos: {medicos}")

        if 'med' in request.GET and request.GET['med']:
            try:
                request.session['med'] = int(request.GET['med'])
            except ValueError:
                request.session['med'] = None

        if request.session.get('med'):
            med = request.session['med']
            medSel = get_object_or_404(Medico, user_id=med)
            horas_medicas = HoraMedica.objects.filter(
                medico=medSel,
                estado='libre',
                f_hra__gt=timezone.now()  # Solo horas futuras
            )

            if not horas_medicas.exists():
                messages.info(request, f"No hay horas médicas disponibles para el médico {medSel.user.first_name} {medSel.user.last_name}.")
            else:
                messages.success(request, f"Para el médico: {medSel.user.first_name} {medSel.user.last_name}. Se han encontrado las siguientes horas médicas: {horas_medicas}")

        try:
            paciente = user.paciente_profile
            return render(request, 'A20_Hrs/solicitar_horapara.html', {
                'especialidades': especialidades,
                'medicos': medicos,
                'horas_medicas': horas_medicas,
                'esp': request.session.get('esp'),
                'med': request.session.get('med'),
                'paciente': paciente,
                'user':user,
            })
        except Paciente.DoesNotExist:
            print('DoesNotExist')
            print(f"esp: {request.session.get('esp')}")
            print(f"med: {request.session.get('med')}")
            messages.error(request, "El usuario no tiene un perfil de paciente.")
            return redirect('home') # Redirige a una página apropiada

    else:
        logger.debug(f"Acceso denegado para usuario: {user.username}") #Log agregado.
        print('Sin acceso')
        print(f"esp: {request.session.get('esp')}")
        print(f"med: {request.session.get('med')}")
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('home')


@login_required
def gestionar_hora(request, paciente_id=None): # Se puede acceder a esta vista con o sin el parámetro paciente_id
    pacientes = Paciente.objects.all()

    if  request.user.groups.filter(name__in=['Pacientes']).exists(): # Si el usuario es un paciente
        try:
            paciente_id = request.user.paciente_profile.pk
            ic(paciente_id)
            paciente = get_object_or_404(Paciente, pk=paciente_id)
            messages.success(request, f"Perfil de paciente {paciente.user.first_name} {paciente.user.last_name} ha sido confirmado!")
        except Http404:
            messages.error(request, "No tienes permiso para acceder a esta página.")
            return redirect('home')

    elif (request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() or request.user.is_superuser): # Si el usuario es Jefe de Plataforma, Recepcionista o Superusuario
            ic('Jefes de Plataforma o Recepcionista')
            try:
                ic('Intentando obtener el perfil de paciente')
                paciente_id = request.GET.get('pac') #Obtener el id del paciente
                ic(paciente_id)
                paciente = get_object_or_404(Paciente, user_id=paciente_id)
                messages.success(request, f"Se gestionará la hora médica para: {paciente.user.first_name} {paciente.user.last_name}")
            except Http404:
                messages.error(request, "Ha habido un erro de Base de Datos de Pacientes.")
                return redirect('home')
    # if paciente_id: # Si se recibe el parámetro paciente_id
    #     if not (request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() or request.user.is_superuser):
    #         messages.error(request, "No tienes permiso para acceder a esta página.")
    #         return redirect('home')
    #     paciente = get_object_or_404(Paciente, pk=paciente_id)
    #     messages.success(request, f"Perfil de paciente {paciente.user.first_name} {paciente.user.last_name} ha sido confirmado!")
    # else: # Si no se recibe el parámetro paciente_id
    #     if (request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() or request.user.is_superuser):
    #         ic('Jefes de Plataforma o Recepcionista')
    #         try:
    #             ic('Intentando obtener el perfil de paciente')
    #             paciente_id = request.GET.get('pac') #Obtener el id del paciente
    #             ic(paciente_id)
    #             paciente = get_object_or_404(Paciente, user_id=paciente_id)
    #             messages.success(request, f"Se gestionará la hora médica para: {paciente.user.first_name} {paciente.user.last_name}")
    #         except Http404:
    #             messages.error(request, "Ha habido un erro de Base de Datos de Pacientes.")
    #             return redirect('home')

    # Limpiar las variables de sesión al inicio de la vista
    request.session.pop('esp', None)
    request.session.pop('med', None)

    especialidades = Especialidad.objects.all()
    medicos = Medico.objects.none()
    horas_medicas = HoraMedica.objects.none()

    if request.method == 'POST':
        if 'liberar_hora' in request.POST:
            hora_medica_id = request.POST.get('hora_medica')
            hora_medica = get_object_or_404(HoraMedica, id=hora_medica_id)
            hora_medica.paciente = None
            hora_medica.estado = 'libre'
            hora_medica.save()
            messages.success(request, "Hora médica liberada exitosamente.")
            return redirect('A20_Hrs:listar_horas_medicas')
        else:
            with transaction.atomic():
                hora_medica_id = request.POST.get('hora_medica')
                hora_medica = get_object_or_404(HoraMedica, id=hora_medica_id)
                hora_medica.paciente = paciente
                hora_medica.estado = 'tomada'
                hora_medica.save()
                messages.success(request, "Hora médica solicitada exitosamente.")
                return redirect('A20_Hrs:listar_horas_medicas')

    if 'esp' in request.GET and request.GET['esp']:
        try:
            request.session['esp'] = int(request.GET['esp'])
        except ValueError:
            request.session['esp'] = None

    if request.session.get('esp'):
        esp = request.session['esp']
        espSel = get_object_or_404(Especialidad, id=esp)
        medicos = Medico.objects.filter(
            especialidad=espSel,
            medico_horas__estado='libre',
            medico_horas__f_hra__gt=timezone.now()
        ).distinct()

        if not medicos.exists():
            messages.info(request, f"No hay médicos con horas disponibles para la especialidad {espSel.name}.")
        else:
            messages.success(request, f"Para la especialidad: {espSel.name}. Se han encontrado los siguientes médicos: {medicos}")

    if 'med' in request.GET and request.GET['med']:
        try:
            request.session['med'] = int(request.GET['med'])
        except ValueError:
            request.session['med'] = None

    if request.session.get('med'):
        med = request.session['med']
        medSel = get_object_or_404(Medico, user_id=med)
        horas_medicas = HoraMedica.objects.filter(
            medico=medSel,
            estado='libre',
            f_hra__gt=timezone.now()  # Solo horas futuras
        )

        if not horas_medicas.exists():
            messages.info(request, f"No hay horas médicas disponibles para el médico {medSel.user.first_name} {medSel.user.last_name}.")
        else:
            messages.success(request, f"Para el médico: {medSel.user.first_name} {medSel.user.last_name}. Se han encontrado las siguientes horas médicas: {horas_medicas}")

    return render(request, 'A20_Hrs/gestionar_hora.html', {
        'pacientes':pacientes,
        'especialidades': especialidades,
        'medicos': medicos,
        'horas_medicas': horas_medicas,
        'esp': request.session.get('esp'),
        'med': request.session.get('med'),
        'paciente': paciente,
    })


@login_required
def liberar_hora(request, paciente_id=None):
    if not (request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() or request.user.is_superuser):
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('home')

    try:
        paciente = get_object_or_404(Paciente, user_id=paciente_id) # Usar user_id en lugar de pk
    except Paciente.DoesNotExist:
        messages.error(request, "Paciente no encontrado.")
        return redirect('A20_Hrs:listar_horas_medicas') # Redirigir a listar_horas_medicas si el paciente no existe

    horas_medicas = HoraMedica.objects.filter(
        paciente=paciente,
        f_hra__gt=ahora, # Asegúrate de que 'ahora' esté definida (probablemente con timezone.now())
        estado='tomada'
    )

    if request.method == 'POST':
        hora_medica_id = request.POST.get('hora_medica_id') # Obtener el ID del input oculto
        try:
            hora_medica = get_object_or_404(HoraMedica, id=hora_medica_id)
            hora_medica.paciente = None
            hora_medica.estado = 'libre'
            hora_medica.save()
            messages.success(request, "Hora médica liberada exitosamente.")
            return redirect('A20_Hrs:listar_horas_medicas') # Redirige a listar_horas_medicas
        except HoraMedica.DoesNotExist:
            messages.error(request, "Hora médica no encontrada.")
            return redirect('A20_Hrs:listar_horas_medicas') # Redirige a listar_horas_medicas si la hora no existe

    return render(request, 'A20_Hrs/liberar_hora.html', {
        'horas_medicas': horas_medicas,
        'paciente': paciente,
    })


@login_required
def ver_horas_paciente(request, paciente_id=None):
    if paciente_id:
        if not (request.user.groups.filter(name__in=['Jefe Plataforma', 'Recepcionista']).exists() or request.user.is_superuser):
            messages.error(request, "No tienes permiso para acceder a esta página.")
            return redirect('home')
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        messages.success(request, f"Perfil de paciente {paciente.user.first_name} {paciente.user.last_name} ha sido confirmado!")
    else:
        try:
            paciente = get_object_or_404(Paciente, user=request.user)
            messages.success(request, "Tu perfil de paciente ha sido confirmado!")
        except Http404:
            messages.error(request, "Usted no tiene perfil de paciente.")
            return redirect('home')
    hoy = date.today()
    horas_medicas = HoraMedica.objects.filter(paciente=paciente, f_hra__gte=hoy).order_by('f_hra')


    if request.method == 'POST':
        if 'liberar_hora' in request.POST:
            hora_medica_id = request.POST.get('hora_medica')
            hora_medica = get_object_or_404(HoraMedica, id=hora_medica_id)
            hora_medica.paciente = None
            hora_medica.estado = 'libre'
            hora_medica.save()
            messages.success(request, "Hora médica liberada exitosamente.")
        elif 'tomar_hora' in request.POST:
            with transaction.atomic():
                hora_medica_id = request.POST.get('hora_medica')
                hora_medica = get_object_or_404(HoraMedica, id=hora_medica_id)
                hora_medica.paciente = paciente
                hora_medica.estado = 'tomada'
                hora_medica.save()
                messages.success(request, "Hora médica tomada exitosamente.")
        return redirect('A20_Hrs:ver_horas_paciente')

    return render(request, 'A20_Hrs/ver_horas_paciente.html', {
        'horas_medicas': horas_medicas,
    })


@login_required
@transaction.atomic
def solicitar_horapara_desdehora(request, hora_medica_id):
    if request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() or request.user.is_superuser:
        pacientes = Paciente.objects.all()
        hora_medica = get_object_or_404(HoraMedica, pk=hora_medica_id)

        if request.method == 'POST':
            paciente_id = request.POST.get('paciente_id')
            paciente = get_object_or_404(Paciente, user_id=paciente_id)
            try:
                with transaction.atomic():
                    # Verificar que la hora médica no esté en el pasado
                    if hora_medica.f_hra < timezone.now():
                        messages.error(request, "No se pueden crear horas médicas en el pasado.")
                        return redirect('A20_Hrs:solicitar_horapara_desdehora', hora_medica_id=hora_medica_id)

                    # Verificar el sistema de salud del paciente
                    if paciente.sistema_salud in hora_medica.medico.sists_salud.all():
                        condicion_pago = "Presentar bono consulta de "+paciente.sistema_salud.name
                    else:
                        condicion_pago = "Pagar en efectivo o con tarjetas un monto de $"+str(hora_medica.costo)

                    # Asignar la hora médica al paciente
                    hora_medica.paciente = paciente
                    hora_medica.estado = 'tomada'
                    hora_medica.save()

                    # Enviar correo electrónico al paciente
                    send_mail(
                        'HumanaSalud-Confirmación de Hora Médica',
                        f'Estimado/a {paciente.user.first_name},\n\nSu hora médica ha sido tomada exitosamente.\n\n\n\nDetalles de su hora en HumanaSalud\n\nMédico: {hora_medica.medico.user.first_name} {hora_medica.medico.user.last_name}\nFecha y Hora: {hora_medica.f_hra}\nCondiciones de Pago: {condicion_pago}\n\nGracias por confiar en nosotros.',
                        settings.DEFAULT_FROM_EMAIL,
                        [paciente.user.email],
                        fail_silently=False,
                    )

                    messages.success(request, f"Hora médica solicitada exitosamente para {paciente.user.first_name} {paciente.user.last_name}.")
                    # return redirect('A20_Hrs:ver_horasmedico', medico_id=hora_medica.medico.user.id, fecha=hora_medica.f_hra.date())
                    return redirect(reverse('A20_Hrs:ver_horasmedico', kwargs={
                        'medico_id': hora_medica.medico.user.id,
                        'fecha': hora_medica.f_hra.strftime('%Y-%m-%d_%H:%M'), # Formatea la fecha y hora
                    }))

            except OperationalError as e:  # Captura la excepción OperationalError
                if "database is locked" in str(e):
                    messages.error(request, "La base de datos está bloqueada. Inténtalo de nuevo más tarde.")
                    return redirect('A20_Hrs:listar_horas_medicas')  # Redirige a la lista de horas
                else:
                    raise  # Re-lanza otras excepciones OperationalError

            except ValueError as e: # Captura la excepción ValueError
                messages.error(request, str(e)) # Muestra el mensaje de error
                return redirect('A20_Hrs:solicitar_horapara_desdehora', hora_medica_id=hora_medica_id) # Redirige a la misma página

            except Exception as e: # Captura cualquier otra excepción
                messages.error(request, "Ocurrió un error inesperado: " + str(e))
                return redirect('A20_Hrs:listar_horas_medicas')  # Redirige a la lista de horas


        return render(request, 'A20_Hrs/solicitar_horapara_desdehora.html', {
            'pacientes': pacientes,
            'hora_medica': hora_medica,
        })
    else:
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('home')


######################################################################################



@login_required
def filtro_calendario_horasmedicas(request):
    medico_id = request.GET.get('medico')
    especialidad_id = request.GET.get('especialidad')
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month', datetime.now().month)

    # Guardar los filtros en la sesión
    request.session['medico_id'] = medico_id
    request.session['especialidad_id'] = especialidad_id

    query_params = f'?year={year}&month={month}'
    if medico_id:
        query_params += f'&medico={medico_id}'
    if especialidad_id:
        query_params += f'&especialidad={especialidad_id}'

    return redirect(f'/horas_medicas/calendario/{query_params}')


@login_required # Ok
def calendario_horasmedicas(request):

    # Anular horas médicasque no fueron tomadas
    # estado = 'libre'y fecha menor a la fecha actual
    actualizar_horas_anular()

    # Obtener todos los médicos y especialidades
    medicos = Medico.objects.all()
    especialidades = Especialidad.objects.all()

    # Obtener los filtros de la sesión
    medico_id = request.session.get('medico_id') # Obtener el valor de la variable 'medico_id' de la sesión
    medico_id = request.GET.get('medico') # Obtener el valor de la variable 'medico' de la URL
    request.session['medico_id'] = medico_id # Guardar el valor de 'medico_id' en la sesión

    especialidad_id = request.session.get('especialidad_id')
    especialidad_id = request.GET.get('especialidad')
    request.session['especialidad_id'] = especialidad_id

    day = request.GET.get('dia')

    # Obtener el mes y año actual o de los parámetros de consulta
    now = timezone.now() # Fecha actual aware o sea considera info de zona horaria que es requisito en settings  USE_TZ = True
    ic(now,type(now))
    
    year = request.GET.get('year', now.year) # Obtener el valor de la variable 'year' de la URL o el valor por defecto 'now.year'
    month = request.GET.get('month', now.month)

    # Convertir los parámetros a enteros si son cadenas
    if isinstance(year, str):
        year = year.replace('\xa0', '').strip()
    if isinstance(month, str):
        month = month.replace('\xa0', '').strip()
    try:
        year = int(year)
        month = int(month)
    except ValueError:
        year = now.year
        month = now.month

    # Si se selecciona un día, mostrar el template específico del día
    if day:
        try:
            day = datetime.strptime(day, '%Y-%m-%d').date() # Convertir la cadena en un objeto date de Python (datetime.date) con el formato 'YYYY-MM-DD' (ej. '2021-12-31')
            return redirect('A20_Hrs:horasmedicas_x_dia', year=day.year, month=day.month, day=day.day)
        except ValueError:
            raise Http404("Fecha no válida")


    # query_params = f'?year={year}&month={month}'
    # if medico_id:
    #     query_params += f'&medico={medico_id}'
    # if especialidad_id:
    #     query_params += f'&especialidad={especialidad_id}'


    # Obtener el primer y último día del mes
    first_day_of_month = datetime(year, month, 1).date()
    # Calcular el primer día del mes siguiente
    if month == 12:
        first_day_of_next_month = datetime(year + 1, 1).date()
    else:
        first_day_of_next_month = datetime(year, month + 1, 1).date()


    # Filtrar horas médicas según rol y filtros seleccionados
    horas_medicas = HoraMedica.objects.filter(
        f_hra__gte=first_day_of_month,
        f_hra__lt=first_day_of_next_month,
    ).exclude(estado__in=['anulada','perdida'])

    # if not request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionistas']).exists() and not request.user.is_superuser:
    #     messages.error(request,"No tienes permisos para realizar esta acción")
    #     return redirect('home')


    if request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionistas']).exists():
        messages.info(request,"Haz ingresado como Jefe de Plataforma o Recepcionista")
        pass  # Pueden ver todas las horas
    elif request.user.groups.filter(name__in=['Medicos']).exists():
        horas_medicas = horas_medicas.filter(medico=request.user.medico_profile)
        for hora in horas_medicas:
            ic(hora.f_hra,type(hora.f_hra))
        messages.info(request,"Acceso acreditado como Médico")
    elif request.user.groups.filter(name__in=['Pacientes']).exists():
        horas_medicas = horas_medicas.filter(paciente=request.user.paciente_profile)
        messages.info(request,"Acceso acreditado como Paciente")
    else:
        messages.error(request,"No cuentas con los permisos necesarios para acceder a esta página")
        return redirect('home')


    if medico_id:
        horas_medicas = horas_medicas.filter(medico_id=medico_id)
    elif especialidad_id:
        horas_medicas = horas_medicas.filter(medico__especialidad__id=especialidad_id)

    # Crear un diccionario para almacenar las horas médicas por día
    calendario = defaultdict(list)
    for hora in horas_medicas:
        day = hora.f_hra.day
        calendario[day].append(hora)

    # Filtrar médicos por especialidad si se selecciona una especialidad
    if especialidad_id:
        medicos = medicos.filter(especialidad__id=especialidad_id).distinct()

    # Crear una lista de semanas para el calendario
    semanas = []
    current_week = []

    # Agregar celdas vacías al principio de la primera semana si el primer día del mes no es lunes
    first_weekday = first_day_of_month.weekday()
    for _ in range(first_weekday):
        current_week.append((None, []))

    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        date = datetime(year, month, day)
        current_week.append((date, calendario[day]))
        if date.weekday() == 6:  # Domingo
            semanas.append(current_week)
            current_week = []
    if current_week:
        semanas.append(current_week)

    # Calcular el número de celdas vacías para completar cada semana
    for semana in semanas:
        while len(semana) < 7:
            semana.append((None, []))

    # Calcular el mes anterior y el siguiente
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    # Obtener el nombre del mes actual en español
    month_name = format_date(first_day_of_month, 'MMMM', locale='es')
    month_actual=now.month

    return render(request, 'A20_Hrs/calendario_horasmedicas.html', {
        'day':day,
        'dia':date,
        'semanas': semanas,
        'year': year,
        'month': month,
        'month_name': month_name,
        'month_actual': month_actual,
        'medicos': medicos,
        'especialidades': especialidades,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'selected_medico': int(medico_id) if medico_id else None,
        'selected_especialidad': int(especialidad_id) if especialidad_id else None,
        'medico_id': medico_id,
        'especialidad_id': especialidad_id,
        'now':now,
    })


@login_required
def horasmedicas_x_dia(request, year, month, day):
    try:
        day = datetime(year, month, day).date()
    except ValueError:
        raise Http404("Fecha no válida")

    horas_medicas = HoraMedica.objects.filter(f_hra__date=day)


    if request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists():
        pass  # Pueden ver todas las horas
    elif request.user.groups.filter(name__in=['Medico']).exists():
        horas_medicas = horas_medicas.filter(medico=request.user.medico_profile)
    elif request.user.groups.filter(name__in=['Paciente']).exists():
        horas_medicas = horas_medicas.filter(paciente=request.user.paciente_profile)
    else:
        messages.error(request,"No cuentas con los permisos necesarios para acceder a esta página")
        return redirect('home')

    return render(request, 'A20_Hrs/horasmedicas_x_dia.html', {'horas_medicas': horas_medicas, 'dia': day})


@login_required
def horamedicaVer(request, hora_id):
    hora = get_object_or_404(HoraMedica, pk=hora_id)
    return render(request, 'A20_Hrs/horamedica_ver.html', {'hora': hora})

@login_required
def calendario_medico(request):
    # Actualizar el estado de las horas médicas en el pasado
    actualizar_horas_anular() #las libres y tomadas son anuladas pero, las pagadas no iniciadas son perdidas
    medico = Medico.objects.get(user=request.user)

    # Obtener el mes y año actual o de los parámetros de consulta
    now = datetime.now()
    year = request.GET.get('year', now.year)
    month = request.GET.get('month', now.month)

    # Convertir los parámetros a enteros si son cadenas
    if isinstance(year, str):
        year = year.replace('\xa0', '').strip()
    if isinstance(month, str):
        month = month.replace('\xa0', '').strip()
    try:
        year = int(year)
        month = int(month)
    except ValueError:
        year = now.year
        month = now.month

    # Obtener el primer y último día del mes
    first_day_of_month = datetime(year, month, 1)
    # Calcular el primer día del mes siguiente
    if month == 12:
        first_day_of_next_month = datetime(year + 1, 1)
    else:
        first_day_of_next_month = datetime(year, month + 1, 1)

    horas_medicas = HoraMedica.objects.filter(
        medico=medico,
        f_hra__gte=first_day_of_month,
        f_hra__lt=first_day_of_next_month,
        # estado='tomada'
    )

    # Crear un diccionario para almacenar las horas médicas por día
    calendario = defaultdict(list)

    for hora in horas_medicas:
        day = hora.f_hra.day
        calendario[day].append(hora)

    # Crear una lista de semanas para el calendario
    semanas = []
    current_week = []

    # Agregar celdas vacías al principio de la primera semana si el primer día del mes no es lunes
    first_weekday = first_day_of_month.weekday()
    for _ in range(first_weekday):
        current_week.append((None, []))

    dias_del_mes = []  # Lista para almacenar los días del mes
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        date = datetime(year, month, day) # Crear un objeto datetime para el día
        try:
            dia_dict = {  # Crea el diccionario *aquí*
            'date': date,
            'date_str': dateformat.format(date, 'Y-m-d')
            }
            dias_del_mes.append(dia_dict)  # Agrega el diccionario a la lista

            current_week.append((dia_dict, calendario[day]))  # Usa el diccionario en current_week

        except ValueError:
            pass

        if date.weekday() == 6:  # Domingo
            semanas.append(current_week)
            current_week = []

    if current_week:
        semanas.append(current_week)

    # Calcular el número de celdas vacías para completar cada semana
    for semana in semanas:
        while len(semana) < 7:
            semana.append((None, []))

    # Calcular el mes anterior y el siguiente
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    # Obtener el nombre del mes actual en español
    month_name = format_date(first_day_of_month, 'MMMM', locale='es')
    print(semanas)
    now = timezone.now()  # Fecha actual aware o sea considera info de zona horaria que es requisito en settings  USE_TZ = True
    print("##$%$#$%$#$%  NOW ###############   ",type(now))

    return render(request, 'A20_Hrs/calendario_medico.html', {
        'dias': dias_del_mes,
        'semanas': semanas,
        'year': year,
        'month': month,
        'month_name': month_name,
        'medico': medico,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'now': now,
    })


# @login_required
# def ver_horasmedico(request, medico_id, fecha):
#     try:
#         hoy =date.today()
#         fechaif = datetime.strptime(fecha, '%Y-%m-%d_%H:%M').date()
#         if fechaif == hoy:
#             # fecha = datetime.strptime(fecha, '%Y-%m-%d_%H:%M').date() # Convertir la fecha de cadena a objeto datetime
#             fecha_dt = datetime.strptime(fecha, '%Y-%m-%d_%H:%M') # Formato de fecha y hora
#         else:
#             messages.error(request, "No se puede ver horas médicas de días anteriores, ni futuras.")
#             return redirect('A20_Hrs:calendario_horasmedicas')
#     except ValueError:
#         raise Http404("Fecha y hora no válidas!!")

#     try:
#         medico = get_object_or_404(Medico, user_id=medico_id)
#     except Exception as e:
#         messages.error(request, f"Error al obtener médico: {e}")
#         return redirect('A20_Hrs:calendario_horasmedicas')

#     horas_medicas = HoraMedica.objects.filter(
#             medico=medico,
#             f_hra__date=fecha_dt.date(),
#             estado='tomada'
#             )

#     return render(request, 'A20_Hrs/ver_horasmedico.html', {
#             'medico': medico,
#             'horas_medicas': horas_medicas,
#             'fecha': fecha_dt.date(),
#             'hora': fecha_dt.time(),
#             })

@login_required
def ver_horasmedico(request, medico_id, fecha):
    try:
        # Intentar convertir la fecha con el formato original
        try:
            fecha_dt = timezone.datetime.strptime(fecha, '%Y-%m-%d_%H:%M')
        except ValueError:
            # Si falla, intentar con el formato de la URL
            fecha_dt = timezone.datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S%z')

        # Asegurar que la fecha sea "aware"
        if timezone.is_naive(fecha_dt):
            fecha_dt = timezone.make_aware(fecha_dt)

        hoy = timezone.now().date()

        if fecha_dt.date() == hoy:
            medico = get_object_or_404(Medico, user_id=medico_id)
            horas_medicas = HoraMedica.objects.filter(
                medico=medico,
                f_hra__date=fecha_dt.date(),
                estado__in=['tomada','pagada']
            )

            return render(request, 'A20_Hrs/ver_horasmedico.html', {
                'medico': medico,
                'horas_medicas': horas_medicas,
                'fecha': fecha_dt.date(),
                'hora': fecha_dt.time(),
            })
        else:
            messages.error(request, "No se puede ver horas médicas de días anteriores, ni futuras.")
            return redirect('A20_Hrs:calendario_horasmedicas')
    except ValueError:
        raise Http404("Fecha y hora no válidas!!")


@login_required
def editar_hora_medica(request, hora_medica_id):
    if not request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() and not request.user.is_superuser:
        messages.error(request, "No tienes permisos para realizar esta acción")
        return redirect('home')
    hora_medica = get_object_or_404(HoraMedica, pk=hora_medica_id)
    if request.method == 'POST':
        form = EditarHoraMedicaForm(request.POST, instance=hora_medica)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, 'Hora médica editada correctamente.')
                    return redirect('A20_Hrs:listar_horas_medicas')
            except Exception as e:
                messages.error(request, f"Error al editar la hora médica: {e}")
        else:
            messages.error(request, "Por favor, corrige los errores en el formulario.")
    else:
        form = EditarHoraMedicaForm(instance=hora_medica)
    return render(request, 'A20_Hrs/editar_hora_medica.html', {'form': form, 'hora_medica': hora_medica})


@login_required
def eliminar_hora_medica(request, hora_medica_id):
    if not request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() and not request.user.is_superuser:
        messages.error(request, "No tienes permisos para realizar esta acción")
        return redirect('home')
    hora_medica = get_object_or_404(HoraMedica, pk=hora_medica_id)
    try:
        hora_medica.estado = 'anulada'
        hora_medica.save()
        messages.success(request, 'Hora médica anulada correctamente.')
    except Exception as e:
        messages.error(request, f"Error al anular la hora médica: {e}")
    return redirect('A20_Hrs:listar_horas_medicas')



###################  PAGOS  ####################
logger = logging.getLogger(__name__)
@login_required
def registrar_pago_efectivo(request, hora_medica_id):
    logger.debug(f"Iniciando registro de pago en efectivo para hora_medica_id: {hora_medica_id}") #log agregado
    ic(hora_medica_id)
    hora_medica = get_object_or_404(HoraMedica, pk=hora_medica_id)
    ic(hora_medica)
    logger.debug(f"Hora médica recuperada: {hora_medica}") #log agregado
    if not (request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() or request.user.is_superuser):
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('home')

    if hora_medica.pagada:  # Verifica si la hora ya fue pagada
        messages.warning(request, "Esta hora médica ya ha sido pagada.")
        return redirect('A20_Hrs:calendario_horasmedicas')  # Redirige a la lista de horas

    try:
        with transaction.atomic():  # Usar atomic para asegurar la integridad
            pago = Pago.objects.create(  # Crea el pago directamente
                hora_medica     = hora_medica,
                tipo_pago       = 'efectivo',
                monto           = hora_medica.costo,
            )
            hora_medica.pagada = True
            hora_medica.estado = 'pagada'
            hora_medica.save()

            logger.debug(f"Pago registrado exitosamente para hora médica: {hora_medica}") #log agregado
            messages.success(request, "Pago en efectivo registrado exitosamente. Hora médica puede ser atendida.")
            return redirect('A20_Hrs:calendario_horasmedicas')

    except Exception as e:
        logger.error(f"Error al registrar el pago: {e}") #log agregado
        messages.error(request, f"Ocurrió un error al registrar el pago: {e}")
        return redirect('A20_Hrs:calendario_horasmedicas')

@login_required
def registrar_pago_bono(request, hora_medica_id):
    hora_medica = get_object_or_404(HoraMedica, pk=hora_medica_id)

    if not (request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() or request.user.is_superuser):
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('home')

    if hora_medica.pagada:  # Verifica si la hora ya fue pagada
        messages.warning(request, "Esta hora médica ya ha sido pagada.")
        return redirect('A20_Hrs:calendario_horasmedicas')  # Redirige a la lista de horas

    if request.method == 'POST':  # Para recibir datos del bono (ej: número de bono)
        numero_bono = request.POST.get('numero_bono')  # Obtén el número de bono del formulario

        try:
            with transaction.atomic():
                pago = Pago.objects.create(
                    hora_medica=hora_medica,
                    monto=hora_medica.costo,  # El monto del bono debería ser el mismo que el costo de la hora
                    tipo_pago='bono',
                    sistema_salud=hora_medica.paciente.sistema_salud  # Asocia el sistema de salud del médico (o el del paciente si lo tienes)
                    # ... otros campos si es necesario (ej: número de transacción, etc.)
                )
                hora_medica.pagada = True
                hora_medica.estado = 'pagada'
                hora_medica.save()

                messages.success(request, "Pago con bono registrado exitosamente.")
                return redirect('A20_Hrs:calendario_horasmedicas')

        except Exception as e:
            messages.error(request, f"Ocurrió un error al registrar el pago con bono: {e}")
            return redirect('A20_Hrs:calendario_horasmedicas')
        except Http404:
            return render(request, '404.html', status=404)  # Renderiza tu template 404

    # Si no es POST, renderiza el template con el formulario para ingresar el número de bono
    return render(request, 'A20_Hrs/registrar_pago_bono.html', {'hora_medica': hora_medica})

@login_required
def registrar_pago_tarjeta(request, hora_medica_id):
    hora_medica = get_object_or_404(HoraMedica, pk=hora_medica_id)

    if not (request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() or request.user.is_superuser):
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('home')

    if hora_medica.pagada:  # Verifica si la hora ya fue pagada
        messages.warning(request, "Esta hora médica ya ha sido pagada.")
        return redirect('A20_Hrs:calendario_horasmedicas')  # Redirige a la lista de horas

    if request.method == 'POST':  # Para recibir datos de la tarjeta (ej: número de tarjeta, etc.)
        numero_tarjeta = request.POST.get('numero_tarjeta')  # Obtén el número de tarjeta del formulario
        numero_transaccion = request.POST.get('numero_transaccion')  # Obtén el número de transacción del formulario
        # ... otros datos de la tarjeta (fecha de expiración, código de seguridad, etc.)

        try:
            with transaction.atomic():
                pago = Pago.objects.create(
                    hora_medica=hora_medica,
                    monto=hora_medica.costo,  # El monto de la tarjeta debería ser el mismo que el costo de la hora
                    tipo_pago='tarjeta',
                    numero_tarjeta=numero_tarjeta,
                    numero_transaccion=numero_transaccion,
                    # ... otros campos si es necesario (ej: número de transacción, etc.)
                )
                hora_medica.pagada = True
                hora_medica.estado = 'pagada'
                hora_medica.save()

                messages.success(request, "Pago con tarjeta registrado exitosamente.")
                return redirect('A20_Hrs:calendario_horasmedicas')

        except Exception as e:
            messages.error(request, f"Ocurrió un error al registrar el pago con tarjeta: {e}")
            return redirect('A20_Hrs:calendario_horasmedicas')
        except Http404:
            return render(request, '404.html', status=404)  # Renderiza tu template 404

    # Si no es POST, renderiza el template con el formulario para ingresar los datos de la tarjeta
    return render(request, 'A20_Hrs/registrar_pago_tarjeta.html', {'hora_medica': hora_medica})



##############################INFORMES#############################################
@login_required
def informe_diario_horas_medicas(request):
    fecha_actual = timezone.localtime(timezone.now()).date()
    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')  # Establecer idioma local a español
    fecha_formateada = fecha_actual.strftime("%A, %d de %B de %Y")  # Formato lunes, 02 de marzo de 2025
    pagos_del_dia = Pago.objects.filter(fecha_pago__date=fecha_actual).select_related('hora_medica__medico')

    # Diccionarios para subtotales y total (igual que antes)
    subtotales_medico = {}
    subtotales_tipo_pago = {'efectivo': 0, 'bono': 0, 'tarjeta': 0}
    total_diario = 0

    for pago in pagos_del_dia:
        medico = pago.hora_medica.medico
        if medico not in subtotales_medico:                                         #  Verifica si el médico ya está en el diccionario
            subtotales_medico[medico] = {'efectivo': 0, 'bono': 0, 'tarjeta': 0}    # Si no está, crea un nuevo diccionario para el médico
        subtotales_medico[medico][pago.tipo_pago] += pago.monto                     # Suma el monto al tipo de pago correspondiente
        subtotales_tipo_pago[pago.tipo_pago] += pago.monto                          # Suma el monto al tipo de pago correspondiente
        total_diario += pago.monto                                                  # Suma el monto al total diario

    if 'pdf' in request.GET:  # Descarga en PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=8)
        pdf.set_fill_color(220, 118, 51)  # Color de encabezado

        # Encabezado
        pdf.set_font("Helvetica", 'B', size=18)
        pdf.cell(0, 10, txt=f"Informe Diario - {fecha_formateada}", ln=1, align="C", fill=True)  # Encabezado con color

        # Detalle de pagos del día
        pdf.ln()
        pdf.set_font("Helvetica", 'B', size=12)
        pdf.cell(0, 10, txt="Detalle del día", ln=1, align="L")
        pdf.set_font("Helvetica", size=10)
        pdf.set_font("Helvetica", 'B', size=10)
        pdf.cell(40, 10, txt="Médico", border=1, align="C")
        pdf.cell(40, 10, txt="Hora", border=1, align="C")
        pdf.cell(40, 10, txt="Paciente", border=1, align="C")
        pdf.cell(40, 10, txt="Tipo", border=1, align="C")
        pdf.cell(40, 10, txt="Monto", border=1, align="C", ln=1)
        pdf.set_font("Helvetica", size=8)

        for pago in pagos_del_dia:
            pdf.cell(40, 10, txt=f"{pago.hora_medica.medico.user.first_name} {pago.hora_medica.medico.user.last_name}", border=1)
            pdf.cell(40, 10, txt=str(pago.hora_medica.f_hra), border=1, align="C")
            pdf.cell(40, 10, txt=f"{pago.hora_medica.paciente.user.first_name} {pago.hora_medica.paciente.user.last_name}", border=1)
            pdf.cell(40, 10, txt=pago.tipo_pago, border=1, align="C")
            pdf.cell(20, 10, txt=str(pago.monto), border=1, align="C", ln=1)

        # Subtotales por médico
        pdf.ln()
        pdf.set_font("Helvetica", 'B', size=12)
        pdf.cell(0, 10, txt="Subtotales por Médico", ln=1, align="L")
        pdf.set_font("Helvetica", size=10)

        for medico, subtotales in subtotales_medico.items():
            pdf.cell(80, 10, txt=f"{medico.user.first_name} {medico.user.last_name}", border=1)
            pdf.cell(40, 10, txt=f"Efectivo: {subtotales['efectivo']}", border=1, align="C")
            pdf.cell(40, 10, txt=f"Bono: {subtotales['bono']}", border=1, align="C")
            pdf.cell(40, 10, txt=f"Tarjeta: {subtotales['tarjeta']}", border=1, align="C", ln=1)

        # Subtotales por tipo de pago
        pdf.ln()
        pdf.set_font("Helvetica", 'B', size=12)
        pdf.cell(0, 10, txt="Subtotales por Tipo de Pago", ln=1, align="L")
        pdf.set_font("Helvetica", size=10)

        for tipo_pago, monto in subtotales_tipo_pago.items():
            pdf.cell(80, 10, txt=f"{tipo_pago}: {monto}", border=1, align="C", ln=1)


        # Total diario
        pdf.ln()
        pdf.set_font("Helvetica", 'B', size=12)
        pdf.cell(0, 10, txt="Total Diario", ln=1, align="l")
        pdf.cell(80, 10, txt=f"{total_diario}", border=3, align="C", ln=1)
        pdf.set_font("Helvetica", size=10)


        # Crear carpeta si no existe
        ruta_carpeta = os.path.join(settings.MEDIA_ROOT, "InformesAdm/inf_dia")  # Nombre de la carpeta
        if not os.path.exists(ruta_carpeta):
            os.makedirs(ruta_carpeta)

        filename=f"Informe de Ventas x Día-{fecha_actual}.pdf"
        filepath=os.path.join(ruta_carpeta,filename)
        pdf.ln()
        pdf.cell(120, 10, filename, 0)
        pdf.ln()
        pdf.set_font("Helvetica", 'B', size=12)
        pdf.cell(120, 10, "HumanaSalud, tu salud nuestro compromiso." , 0)
        pdf.output(filepath)

        return HttpResponse(bytes(pdf.output()), content_type="application/pdf")

    context = {
        'fecha_actual': fecha_actual,
        'pagos_del_dia': pagos_del_dia,
        'subtotales_medico': subtotales_medico,
        'subtotales_tipo_pago': subtotales_tipo_pago,
        'total_diario': total_diario,
    }

    return render(request, 'A20_Hrs/informe_diario_horas_medicas.html', context)


def calcular_subtotales_y_totales(pagos_del_mes):
    subtotales_medico = {}
    subtotales_tipo_pago = {'efectivo': 0, 'bono': 0, 'tarjeta': 0}
    total_mes = 0

    for pago in pagos_del_mes:
        medico = pago.hora_medica.medico
        subtotales_medico.setdefault(medico, {'efectivo': 0, 'bono': 0, 'tarjeta': 0})[pago.tipo_pago] += pago.monto
        subtotales_tipo_pago[pago.tipo_pago] += pago.monto
        total_mes += pago.monto

    return subtotales_medico, subtotales_tipo_pago, total_mes

def generar_pdf_informe_mensual(mes, mes_formateado, pagos_del_mes, subtotales_medico, subtotales_tipo_pago, total_mes, anio_seleccionado, mes_seleccionado):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=8)
    pdf.set_fill_color(220, 118, 51)  # Color de encabezado

    # Encabezado
    mes_formateado = mes.strftime("%B de %Y")  # Formato: Mes de aaaa
    pdf.set_font("Helvetica", 'B', size=18)
    pdf.cell(0, 10, txt=f"Informe Mensual - {mes_formateado}", ln=1, align="C", fill=True)  # Encabezado con color

    # Tabla de pagos
    pdf.ln()
    pdf.set_font("Helvetica", 'B', size=12)
    pdf.cell(0, 10, txt="Detalle General del Mes", ln=1, align="L")
    pdf.set_font("Helvetica", size=10)
    pdf.set_font("Helvetica", 'B', size=8)
    pdf.cell(50, 10, txt="Médico", border=1, align="C")
    pdf.cell(40, 10, txt="Hora", border=1, align="C")
    pdf.cell(50, 10, txt="Paciente", border=1, align="C")
    pdf.cell(25, 10, txt="Tipo", border=1, align="C")
    pdf.cell(25, 10, txt="Monto", border=1, align="C", ln=1)
    pdf.set_font("Helvetica", size=8)

    for pago in pagos_del_mes:
        fecha_hora_formateada = timezone.localtime(pago.hora_medica.f_hra).strftime("%Y-%m-%d %H:%M")
        pdf.cell(50, 10, txt=f"{pago.hora_medica.medico.user.first_name} {pago.hora_medica.medico.user.last_name}", border=1)
        pdf.cell(40, 10, txt=fecha_hora_formateada, border=1, align="C")
        pdf.cell(50, 10, txt=f"{pago.hora_medica.paciente.user.first_name} {pago.hora_medica.paciente.user.last_name}", border=1)
        pdf.cell(25, 10, txt=pago.tipo_pago, border=1, align="C")
        pdf.cell(25, 10, txt=str(pago.monto), border=1, align="C", ln=1)

    # Subtotales por médico
    pdf.ln()
    pdf.set_font("Helvetica", 'B', size=12)
    pdf.cell(0, 10, txt="Subtotales por Médico", ln=1, align="L")
    pdf.set_font("Helvetica", size=10)

    for medico, subtotales in subtotales_medico.items():
        pdf.cell(50, 10, txt=f"{medico.user.first_name} {medico.user.last_name}", border=1)
        pdf.cell(40, 10, txt=f"Efectivo: {subtotales['efectivo']}", border=1, align="C")
        pdf.cell(40, 10, txt=f"Bono: {subtotales['bono']}", border=1, align="C")
        pdf.cell(40, 10, txt=f"Tarjeta: {subtotales['tarjeta']}", border=1, align="C", ln=1)

    # Subtotales por tipo de pago
    pdf.ln()
    pdf.set_font("Helvetica", 'B', size=12)
    pdf.cell(0, 10, txt="Subtotales por Tipo de Pago", ln=1, align="L")
    pdf.set_font("Helvetica", size=10)

    for tipo_pago, monto in subtotales_tipo_pago.items():
        pdf.cell(80, 10, txt=f"{tipo_pago}: {monto}", border=1, align="C", ln=1)

    # Total mensual
    pdf.ln()
    pdf.set_font("Helvetica", 'B', size=12)
    pdf.cell(0, 10, txt=f"Total Mensual: {total_mes}", ln=1, align="L")
    pdf.set_font("Helvetica", size=10)


    # Crear carpeta si no existe
    ruta_carpeta = os.path.join(settings.MEDIA_ROOT, "InformesAdm/inf_mes")  # Nombre de la carpeta
    if not os.path.exists(ruta_carpeta):
        os.makedirs(ruta_carpeta)

    filename=f"InformeVentasxMes-{anio_seleccionado}-{mes_seleccionado}.pdf" # Nombre del archivo con año y mes
    filepath=os.path.join(ruta_carpeta,filename)
    pdf.cell(120, 10, filepath, 1) # Agregar el nombre del archivo al PDF
    pdf.output(filepath) # Guardar el PDF en la carpeta

    return HttpResponse(bytes(pdf.output()), content_type="application/pdf")


@login_required
def informe_mensual_horas_medicas(request):
    # ... (código para inicializar variables, igual que antes)
    mes = None  # Inicializar la variable mes a None
    pagos_del_mes = None  # Inicializar la variable pagos_del_mes a None
    mes_formateado = None  # Inicializar la variable mes_formateado a None
    consulta_realizada = False # Nueva variable para indicar si se realizó una consulta
    mes_seleccionado = None  # Inicializar mes_seleccionado
    anio_seleccionado = None  # Inicializar anio_seleccionado

    # Diccionarios para subtotales y total
    subtotales_medico = {}
    subtotales_tipo_pago = {'efectivo': 0, 'bono': 0, 'tarjeta': 0}
    total_mes = 0

    if request.method == 'POST':
        mes_seleccionado = request.POST.get('mes')  # Obtener el mes del formulario
        anio_seleccionado= request.POST.get('anio')  # Obtener el año del formulario

        if mes_seleccionado and anio_seleccionado:
            try:
                mes = f"{anio_seleccionado}-{mes_seleccionado}-01" # Formato aaaa-mm-01
                mes = timezone.datetime.strptime(mes, "%Y-%m-%d").date() # Convertir a objeto date
                locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8') # Establecer idioma local a español
                mes_formateado = mes.strftime("%B de %Y")  # Formatear la fecha *aquí*

                # Obtener los pagos del mes
                pagos_del_mes = Pago.objects.filter(fecha_pago__month=mes.month, fecha_pago__year=mes.year).select_related('hora_medica__medico') # Obtener los pagos del mes seleccionado *aquí* (usar select_related para evitar consultas adicionales)

                if pagos_del_mes:
                    subtotales_medico, subtotales_tipo_pago, total_mes = calcular_subtotales_y_totales(pagos_del_mes)
                else:
                    messages.warning(request, "No se encontraron pagos para el mes seleccionado.")

                consulta_realizada = True

            except ValueError:
                messages.error(request, "El mes seleccionado no es válido.")
                mes_formateado ="Error: Formato de fecha es incorrecto."
        else:
            messages.error(request, "Por favor, selecciona un mes y un año.")
            mes_formateado = "Error: Mes y año no seleccionados."

    context = {
        'mes': mes,
        'mes_formateado': mes_formateado,
        'pagos_del_mes': pagos_del_mes,
        'subtotales_medico': subtotales_medico,
        'subtotales_tipo_pago': subtotales_tipo_pago,
        'total_mes': total_mes,
        'consulta_realizada': consulta_realizada,
        'mes_seleccionado': mes_seleccionado,
        'anio_seleccionado': anio_seleccionado,
    }

    if 'pdf' in request.GET:
        mes_seleccionado = request.GET.get('mes')
        anio_seleccionado = request.GET.get('anio')
        if mes_seleccionado and anio_seleccionado:
            try:
                mes = f"{anio_seleccionado}-{mes_seleccionado}-01"  # Formato aaaa-mm-01
                mes = timezone.datetime.strptime(mes, "%Y-%m-%d").date()  # Convertir a objeto date
                locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')  # Establecer idioma local a español
                mes_formateado = mes.strftime("%B de %Y")  # Formatear la fecha

                # Obtener los pagos del mes
                pagos_del_mes = Pago.objects.filter(fecha_pago__month=mes.month, fecha_pago__year=mes.year).select_related('hora_medica__medico')  # Obtener los pagos del mes seleccionado (usar select_related para evitar consultas adicionales)

                if pagos_del_mes:
                    subtotales_medico, subtotales_tipo_pago, total_mes = calcular_subtotales_y_totales(pagos_del_mes)
                    return generar_pdf_informe_mensual(mes, mes_formateado, pagos_del_mes, subtotales_medico, subtotales_tipo_pago, total_mes, anio_seleccionado, mes_seleccionado)
                else:
                    messages.warning(request, "No se encontraron pagos para el mes seleccionado.")
                    return redirect('A20_Hrs:informe_mensual_horas_medicas')

            except ValueError:
                messages.error(request, "El mes seleccionado no es válido.")
                return redirect('A20_Hrs:informe_mensual_horas_medicas')
        else:
            messages.error(request, "Por favor, selecciona un mes y un año.")
            return redirect('A20_Hrs:informe_mensual_horas_medicas')

    return render(request, 'A20_Hrs/informe_mensual_horas_medicas.html', context)


def vistaInfAdm(request):
    return render(request, 'A20_Hrs/vistaInfAdm.html')