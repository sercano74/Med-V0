from django.urls import reverse
from .forms import *
from A20_Hrs.models import HoraMedica, Medico, Paciente
from django.contrib import messages
from datetime import datetime, date
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404 as go404
from icecream import ic

import io
import json
import matplotlib.pyplot as plt
import pdb
import time
import urllib, base64





@login_required
def listar_pacientes_con_horas(request):
    if (request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() or request.user.is_superuser):
        horas_medicas=HoraMedica.objects.filter(estado='tomada').select_related('paciente') #

    elif request.user.groups.filter(name__in=['Medicos']).exists():
        medico = go404(Medico, user=request.user)
        horas_medicas = HoraMedica.objects.filter(medico=medico, estado='tomada').select_related('paciente')

    return render(request, 'A30_Fic/listar_pacientes_con_horas.html', {
        'horas_medicas': horas_medicas,
    })

@login_required
def iniciar_ficha_medica(request, paciente_id):
    medico = go404(Medico, user=request.user)
    user =go404(CustomUser, id=paciente_id)
    paciente = go404(Paciente, user=user.id)
    now = datetime.now()

    if request.method == 'POST':
        altura = request.POST['altura']
        peso = request.POST['peso']
        imc = request.POST.get('imc') # Obtener el IMC calculado en el cliente
        notas = request.POST.get('notas', '')

        FichaMedica.objects.create(
            paciente=paciente,
            medico=medico,
            temperatura=request.POST['temperatura'],
            p_sistolica=request.POST['p_sistolica'],
            p_diastolica=request.POST['p_diastolica'],
            altura=request.POST['altura'],
            peso=request.POST['peso'],
            diagnostico=request.POST['diagnostico'],
            prescripcion=request.POST['prescripcion'],
            imc=imc,
            notas=notas,
            estado='Abierta'
        )
        messages.success(request, "Ficha médica iniciada exitosamente.")
        return redirect('A30_Fic:listar_fichas_medicas')

    return render(request, 'A30_Fic/iniciar_ficha_medica.html', locals())


@login_required
def iniciar_ficha_hora(request, hora_id):
    try:
        hora = go404(HoraMedica, pk = hora_id)
        medico = go404(Medico, pk = hora.medico.pk)
        paciente = go404(Paciente, pk = hora.paciente.pk)
        action_url = reverse('A30_Fic:iniciar_ficha_hora',args=[str(hora_id)])
        now = datetime.now()

        if request.method == 'POST':  # Mueve la creación de la ficha DENTRO del bloque POST
            altura = request.POST['altura']
            peso = request.POST['peso']
            imc = request.POST.get('imc')
            notas = request.POST.get('notas', '')
            temperatura = request.POST.get('temperatura')
            p_sistolica = request.POST.get('p_sistolica')
            p_diastolica = request.POST.get('p_diastolica')
            diagnostico = request.POST.get('diagnostico')
            prescripcion = request.POST.get('prescripcion')
            sintomas = request.POST.get('sintomas')

            FichaMedica.objects.create(
                paciente=paciente,
                medico=medico,
                temperatura=temperatura,
                p_sistolica=p_sistolica,
                p_diastolica=p_diastolica,
                altura=altura,
                peso=peso,
                imc=imc,
                sintomas=sintomas,
                diagnostico=diagnostico,
                prescripcion=prescripcion,
                notas=notas,
                estado='Abierta',
            )
            hora.estado = 'iniciada'
            hora.save()

            messages.success(request, "Ficha médica iniciada exitosamente.")
            return redirect('A20_Hrs:calendario_horasmedicas')
        elif request.method == 'GET':
            return render(request, 'A30_Fic/iniciar_ficha_medica.html', locals())

    except HoraMedica.DoesNotExist:
        messages.error(request, "La hora médica solicitada no existe.")
        return redirect('A20_Hrs:calendario_horasmedicas')


@login_required
def listar_fichas_medicas_ajax(request):
    if request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() or request.user.is_superuser:# Solo jefes de plataforma y superusuarios pueden listar todas las fichas médicas (de todos los pacientes)
        fichas_medicas = FichaMedica.objects.all()
        time.sleep(3) # Simula el proceso interno (¡ahora no bloquea!)
        html_content = render(request, 'A30_Fic/listar_fichas_medicas_tabla.html', {'fichas_medicas': fichas_medicas}).content.decode('utf-8')
        ic(request.user  )
        return JsonResponse({'html': html_content})
    elif request.user.groups.filter(name__in=['Medicos']).exists():
        medico = go404(Medico, user=request.user)
        fichas_medicas = FichaMedica.objects.filter(medico=medico)
        time.sleep(3) # Simula el proceso interno (¡ahora no bloquea!)
        html_content = render(request, 'A30_Fic/listar_fichas_medicas_tabla.html', {'fichas_medicas': fichas_medicas}).content.decode('utf-8')
        return JsonResponse({'html': html_content})
    elif request.user.groups.filter(name__in=['Pacientes']).exists():
        paciente = go404(Paciente, user=request.user)
        fichas_medicas = FichaMedica.objects.filter(paciente=paciente, estado='Cerrada')
        time.sleep(3) # Simula el proceso interno (¡ahora no bloquea!)
        html_content = render(request, 'A30_Fic/listar_fichas_medicas_tabla.html', {'fichas_medicas': fichas_medicas}).content.decode('utf-8')
        return JsonResponse({'html': html_content})
    else:
        return JsonResponse({'error': 'No tienes permiso para acceder a esta página.'}, status=403)

@login_required
def listar_fichas_medicas(request):
    return render(request, 'A30_Fic/listar_fichas_medicas.html')


@login_required
def listar_mis_fichas_medicas(request):

    if request.user.is_superuser:
        messages.info(request, "Acceso a superusuario")
    elif request.user.groups.filter(name__in=['Medicos']).exists():
        medico = go404(Medico, user=request.user)
        fichas_medicas = FichaMedica.objects.filter(medico=medico)
        messages.info(request, "Acceso a medico")
    else:
        messages.error(request, "No tienes permiso para modificar esta ficha médica.")
        return redirect('A30_Fic:listar_fichas_medicas')

    return render(request, 'A30_Fic/listar_mis_fichas_medicas.html', {
        'fichas_medicas': fichas_medicas,
    })


@login_required
def ver_ficha_medica(request, ficha_id):

    try:
        ficha = go404(FichaMedica, id=ficha_id)
        sus_especialidades = ficha.medico.especialidad.all()
        messages.info(request, "Ver ficha médica de " + str(ficha.paciente))
    except FichaMedica.DoesNotExist:    # Si no existe la ficha médica
        messages.error(request, "La ficha médica solicitada no existe.")

    if request.user.is_superuser:
        messages.info(request, "Modificando ficha médica de " + str(ficha.paciente))
    elif request.user.groups.filter(name__in=['Medicos']).exists():
        medico = go404(Medico, user=request.user)
        messages.info(request, "Modificando ficha médica de " + str(ficha.paciente))
    elif request.user.groups.filter(name__in=['Pacientes']).exists():
        messages.info(request, "Ver ficha médica de " + str(ficha.paciente))
        return render(request, 'A30_Fic/ver_ficha_medica.html',locals())
    else:
        messages.error(request, "No tienes permiso para modificar esta ficha médica.")
        return redirect('A30_Fic:listar_fichas_medicas')


    if request.method == 'POST':
        ficha.temperatura = float(request.POST['temperatura'].replace(',', '.'))
        ficha.p_sistolica = int(request.POST['p_sistolica'])
        ficha.p_diastolica = int(request.POST['p_diastolica'])
        ficha.altura = float(request.POST['altura'].replace(',', '.'))
        ficha.peso = float(request.POST['peso'].replace(',', '.'))
        ficha.diagnostico = request.POST['diagnostico']
        ficha.prescripcion = request.POST['prescripcion']
        ficha.notas = request.POST.get('notas', '')
        ficha.estado = request.POST['estado']
        ficha.save()
        messages.success(request, "Ficha médica modificada exitosamente.")
        return redirect('A30_Fic:listar_fichas_medicas')

    return render(request, 'A30_Fic/modificar_ficha_medica.html', {
        'ficha': ficha,
    })


@login_required
def modificar_ficha_medica(request, ficha_id):
    ficha = go404(FichaMedica, id=ficha_id)

    if request.user.is_superuser:
        messages.info(request, "Modificando ficha médica de " + str(ficha.paciente))
    elif request.user.groups.filter(name__in=['Medicos']).exists():
        medico = go404(Medico, user=request.user)
        messages.info(request, "Modificando ficha médica de " + str(ficha.paciente))
    else:
        messages.error(request, "No tienes permiso para modificar esta ficha médica.")
        return redirect('A30_Fic:listar_fichas_medicas')

    if request.method == 'POST':
        ficha.temperatura = float(request.POST['temperatura'].replace(',', '.'))
        ficha.p_sistolica = int(request.POST['p_sistolica'])
        ficha.p_diastolica = int(request.POST['p_diastolica'])
        ficha.altura = float(request.POST['altura'].replace(',', '.'))
        ficha.peso = float(request.POST['peso'].replace(',', '.'))
        ficha.diagnostico = request.POST['diagnostico']
        ficha.prescripcion = request.POST['prescripcion']
        ficha.notas = request.POST.get('notas', '')
        ficha.estado = request.POST['estado']
        ficha.save()
        messages.success(request, "Ficha médica modificada exitosamente.")
        return redirect('A30_Fic:listar_fichas_medicas')

    return render(request, 'A30_Fic/modificar_ficha_medica.html', {
        'ficha': ficha,
    })


@login_required
def reasignar_ficha_medica(request, ficha_id):
    if not (request.user.groups.filter(name__in=['Jefes de Plataforma']).exists() or request.user.is_superuser):  # Solo jefes de plataforma y superusuarios pueden reasignar fichas médicas

        messages.error(request, "No tienes permiso para reasignar esta ficha médica.")
        return redirect('home')

    ficha = go404(FichaMedica, id=ficha_id)
    user_id = ficha.medico.user.id
    user= go404(CustomUser,id=user_id)
    medicos = Medico.objects.exclude(user=user)

    if request.method == 'POST':
        if medicos.exists():
            nuevo_medico_id = request.POST['medico']
            user = go404(CustomUser, id=nuevo_medico_id)
            nuevo_medico = go404(Medico, user=user)
            ficha.medico = nuevo_medico
            ficha.save()
            messages.success(request, "Ficha médica reasignada exitosamente.")
            return redirect('A30_Fic:listar_fichas_medicas')
        else:
            messages.error(request, "No existen médicos para reasignar!!")
            return redirect('A30_Fic:listar_fichas_medicas')

    if not medicos.exists(): # Si no hay médicos disponibles para reasignar
        messages.error(request, "No existen médicos disponibles para reasignar.")
        return redirect('A30_Fic:listar_fichas_medicas')

    return render(request, 'A30_Fic/reasignar_ficha_medica.html', {
        'ficha': ficha,
        'medicos': medicos,
    })


@login_required
def historial_medico(request, paciente_id):
    user = go404(CustomUser, id=paciente_id)
    paciente = go404(Paciente, user=user)
    fichas_medicas = FichaMedica.objects.filter(paciente=paciente).order_by('f_consulta')

    # Preparar datos para los gráficos
    fechas = [ficha.f_consulta.strftime('%Y-%m-%d') for ficha in fichas_medicas]
    pesos = [float(ficha.peso) for ficha in fichas_medicas]
    alturas = [float(ficha.altura) for ficha in fichas_medicas]
    p_sistolicas = [int(ficha.p_sistolica) for ficha in fichas_medicas]
    p_diastolicas = [int(ficha.p_diastolica) for ficha in fichas_medicas]
    medicamentos = [ficha.prescripcion for ficha in fichas_medicas]

    # Generar el gráfico de presiones
    plt.figure(figsize=(10, 5))
    plt.plot(fechas, p_sistolicas, label='Presión Sistólica', marker='o')
    plt.plot(fechas, p_diastolicas, label='Presión Diastólica', marker='o')
    plt.xlabel('Fecha')
    plt.ylabel('Presión (mm Hg)')
    plt.title('Presiones Sistólicas y Diastólicas en el Tiempo')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Guardar el gráfico en un archivo temporal
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)

    return render(request, 'A30_Fic/historial_medico.html', {
        'paciente': paciente,
        'fichas_medicas': fichas_medicas,
        'fechas': json.dumps(fechas),
        'pesos': json.dumps(pesos),
        'alturas': json.dumps(alturas),
        'p_sistolicas': json.dumps(p_sistolicas),
        'p_diastolicas': json.dumps(p_diastolicas),
        'medicamentos': medicamentos,
        'grafico_presiones': uri,
    })

