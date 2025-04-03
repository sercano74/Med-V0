import os

from .models import *
from A20_Hrs.models import HoraMedica, Medico, Paciente
from datetime import datetime, date, timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail,EmailMultiAlternatives
from django.http import HttpResponse
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404 as go404
from django.urls import reverse
from django.utils import timezone
from email.message import EmailMessage
from fpdf import FPDF  # Importa FPDF
from icecream import ic
from matplotlib.widgets import Cursor

import io, base64, urllib.parse
import json
import logging
import matplotlib.pyplot as plt
import pandas as pd
import pdb
import time
import traceback
import urllib, base64
import numpy as np
from scipy.interpolate import interp1d

logger = logging.getLogger('envio_email')

# Create your views here.

@login_required
def consultas_ajax(request):
    user = request.user
    consultas = Consulta.objects.none()  # Inicializa un queryset vacío
    if request.user.groups.filter(name__in=['Jefes de Plataforma', 'Recepcionista']).exists() or request.user.is_superuser:
        consultas = Consulta.objects.all()

    elif request.user.groups.filter(name__in=['Medicos']).exists():
        medico = go404(Medico, user=user)
        consultas = Consulta.objects.filter(hora_medica__medico=medico) # Filtra las consultas del médico logueado

    elif request.user.groups.filter(name__in=['Pacientes']).exists():
        paciente = go404(Paciente, user=user)
        consultas = Consulta.objects.filter(hora_medica__paciente=paciente) # Filtra las consultas del paciente logueado que estén finalizadas
    else:
        messages.error(request, 'No tiene permisos para ver esta página')
        return HttpResponseRedirect(reverse('home'))

    time.sleep(2) # Simula el proceso interno (¡ahora no bloquea!)
    html_content = render(request, 'A31_Con/consultas_ajax.html', {'consultas': consultas}).content.decode('utf-8')
    return JsonResponse({'html': html_content})

@login_required
def consultas(request):
    return render(request, 'A31_Con/consultas.html')


@login_required
def consulta_iniciar(request, hora_id):
    try:
        hora = go404(HoraMedica, pk=hora_id)
        if not hora.pagada or hora.estado != 'pagada':
            messages.error(request, "La hora médica no está pagada.")
            return redirect('A20_Hrs:calendario_horasmedicas')
        medico = go404(Medico, pk=hora.medico.pk)
        paciente = go404(Paciente, pk=hora.paciente.pk)

        now = timezone.now()
        if hora.f_hra < now:
            messages.error(request, "No se puede iniciar una consulta para una hora médica pasada.")
            return redirect('A20_Hrs:calendario_horasmedicas')

        examenes = Examen.objects.all()
        medicamentos = Medicamento.objects.filter(estado='activo')  # Obtén los medicamentos activos

        # Manejo de la selección de medicamentos con AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            if 'seleccionar_medicamento' in request.GET:
                medicamento_id = request.GET['seleccionar_medicamento']
                if 'medicamentos_seleccionados' not in request.session:
                    request.session['medicamentos_seleccionados'] = []
                if medicamento_id not in request.session['medicamentos_seleccionados']:
                    request.session['medicamentos_seleccionados'].append(medicamento_id)
                request.session.modified = True
                return JsonResponse({'status': 'ok'})
            elif 'deseleccionar_medicamento' in request.GET:
                medicamento_id = request.GET['deseleccionar_medicamento']
                if 'medicamentos_seleccionados' in request.session:
                    if medicamento_id in request.session['medicamentos_seleccionados']:
                        request.session['medicamentos_seleccionados'].remove(medicamento_id)
                    request.session.modified = True
                return JsonResponse({'status': 'ok'})

        # Obtener medicamentos seleccionados de la sesión
        medicamentos_seleccionados_ids = request.session.get('medicamentos_seleccionados', [])
        medicamentos_seleccionados = Medicamento.objects.filter(id__in=medicamentos_seleccionados_ids)

        if hora.pagada and hora.f_hra.date() == now.date():  # Verifica si está pagada y es hoy

            if request.method == 'POST':
                # Guardar datos del formulario en la sesión
                consulta_data = request.session.get('consulta_data', {})
                consulta_data.update({
                    'temperatura': request.POST.get('temperatura'),
                    'p_sistolica': request.POST.get('p_sistolica'),
                    'p_diastolica': request.POST.get('p_diastolica'),
                    'altura': request.POST.get('altura'),
                    'peso': request.POST.get('peso'),
                    'imc': request.POST.get('imc'),
                    'notas': request.POST.get('notas'),
                    'sintomas': request.POST.get('sintomas'),
                    'diagnostico': request.POST.get('diagnostico'),
                    'observaciones': request.POST.get('observaciones'),
                    'examenes': request.POST.getlist('examenes'),
                    'lugar_emision': request.POST.get('lugar_emision'),
                    'dirigido_a': request.POST.get('dirigido_a'),
                    'antecedentes': request.POST.get('antecedentes'),
                    'diagnosis': request.POST.get('diagnosis'),
                    'inicio': request.POST.get('inicio'),
                    'termino': request.POST.get('termino'),
                })
                request.session['consulta_data'] = consulta_data
                request.session.modified = True

                altura = float(request.POST['altura']) / 100  # Convertir a metros
                peso = float(request.POST['peso'])
                imc = peso / (altura * altura)  # Calcular el IMC
                notas = request.POST.get('notas', '')
                temperatura = request.POST.get('temperatura')
                p_sistolica = request.POST.get('p_sistolica')
                p_diastolica = request.POST.get('p_diastolica')
                diagnostico = request.POST.get('diagnostico')
                sintomas = request.POST.get('sintomas')
                observaciones = request.POST.get('observaciones', '')  # Obtén las observaciones
                examenes_seleccionados = request.POST.getlist('examenes')  # Obtén los exámenes seleccionados
                recomendaciones = request.POST.get('recomendaciones', '')

                consulta = Consulta.objects.create(
                    hora_medica=hora,  # Asocia la consulta con la hora médica
                    temperatura=temperatura,
                    p_sistolica=p_sistolica,
                    p_diastolica=p_diastolica,
                    altura=altura,
                    peso=peso,
                    imc=imc,
                    notas=notas,
                    diagnostico=diagnostico,
                    sintomas=sintomas,
                    observaciones=observaciones,
                    estado='Iniciada'  # O el estado que desees
                )

                # Guardar medicamentos seleccionados
                if medicamentos_seleccionados:
                    consulta.had_receta=True
                    for medicamento in medicamentos_seleccionados:
                        via = request.POST.get(f'via_{medicamento.id}')
                        dosis = request.POST.get(f'dosis_{medicamento.id}')
                        frecuencia = request.POST.get(f'frecuencia_{medicamento.id}')
                        duracion = request.POST.get(f'duracion_{medicamento.id}')
                        Consulta_Receta.objects.create(
                            consulta=consulta,
                            medicamento=medicamento,
                            via=via,
                            dosis=dosis,
                            frecuencia=frecuencia,
                            duracion=duracion
                        )

                # Verificar si la sección de exámenes está activa
                if request.POST['exams_activa'] == 'true':
                    if examenes_seleccionados:  # Verifica si se seleccionaron exámenes
                        consulta.had_OrdExams = True
                        for examen_id in examenes_seleccionados:
                            examen = Examen.objects.get(pk=examen_id)
                            Consulta_Examen.objects.create(consulta=consulta, examen=examen, estado='solicitado')

                # Verificar si la sección de la licencia médica está activa
                if request.POST['licencia_activa'] == 'true':
                    # Validar los campos de la licencia médica
                    if not all([request.POST['lugar_emision'], request.POST['dirigido_a'], request.POST['email_empleador'], request.POST['antecedentes'], request.POST['diagnosis'], request.POST['inicio'], request.POST['termino']]):
                        messages.error(request, "Por favor, complete todos los campos de la licencia médica.")
                        return redirect('A31_Con:consulta_iniciar', hora_id=hora_id)

                    # Crear el objeto Consulta_Certificado
                    Consulta_Certificado.objects.create(
                        consulta=consulta,
                        lugar_emision=request.POST['lugar_emision'],
                        dirigido_a=request.POST['dirigido_a'],
                        email_empleador=request.POST['email_empleador'],
                        antecedentes=request.POST['antecedentes'],
                        diagnosis=request.POST['diagnosis'],
                        recomendaciones=recomendaciones,
                        inicio=request.POST['inicio'],
                        termino=request.POST['termino'],
                    )
                    consulta.had_Certificado = True
                    consulta.save()  # Guarda los cambios en la consulta

                hora.estado = 'iniciada'
                hora.save()

                # Limpiar datos de la sesión después de guardar la consulta
                del request.session['consulta_data']

                messages.success(request, "Consulta iniciada exitosamente.")
                return redirect('A31_Con:consulta_detalle', consulta_id=consulta.id)

            # Rellenar el formulario con datos de la sesión (si existen)
            consulta_data = request.session.get('consulta_data', {})
            return render(request, 'A31_Con/consulta_iniciar.html', locals())

        else:
            messages.error(request, "La hora médica no está pagada o no es hoy.")
            return redirect('A20_Hrs:calendario_horasmedicas')

    except HoraMedica.DoesNotExist:
        messages.error(request, "La hora médica solicitada no existe.")
        return redirect('A20_Hrs:calendario_horasmedicas')


@login_required
def consulta_editar(request, consulta_id):
    consulta = go404(Consulta, pk=consulta_id)

    # Verificar si el usuario es médico y si la consulta está asociada a su hora médica
    if not request.user.is_superuser and (not request.user.groups.filter(name='Medicos').exists() or consulta.hora_medica.medico.user != request.user):
        messages.error(request, "No tiene permisos para editar esta consulta.")
        return redirect('A31_Con:consulta_detalle', consulta_id=consulta_id)

    examenes = Examen.objects.all()
    medicamentos = Medicamento.objects.filter(estado='activo')

    if request.method == 'POST':
        print('Entramos al POST!!!')

        # Imprimir los datos recibidos en la solicitud POST
        # print(request.POST)
        try:
            # Actualizar datos de la consulta
            if request.POST['temperatura']or request.POST['p_sistolica']or request.POST['p_diastolica']or request.POST['peso']or request.POST['altura']:
                temperatura_str = request.POST['temperatura'].replace(',', '.')
                consulta.temperatura = round(float(temperatura_str),2)
                peso_str = request.POST['peso'].replace(',', '.') #replace comma with point
                peso = float(peso_str)
                altura_str = request.POST['altura'].replace(',', '.') #replace comma with point
                altura = float(altura_str)

                consulta.p_sistolica = request.POST['p_sistolica']
                consulta.p_diastolica = request.POST['p_diastolica']
                consulta.altura = altura
                consulta.peso = peso
                if altura>0:
                    consulta.imc = round(float(peso / ((altura / 100) ** 2)),2)
                else:
                    consulta.imc = 0
                consulta.notas = request.POST['notas']
                consulta.sintomas = request.POST['sintomas']
                consulta.diagnostico = request.POST['diagnostico']
                consulta.observaciones = request.POST['observaciones']
                consulta.estado = request.POST['estado']  # Permitir cambiar el estado
                print('Vamos a grabar la consulta !!!')
                consulta.save()
                consulta = go404(Consulta, pk=consulta_id)
                print('consulta',consulta)

            # Actualizar medicamentos
            if request.POST.getlist('medicamentos'):
                medicamentos_seleccionados = request.POST.getlist('medicamentos')
                print('Tenemos medicamentos seleccionados!!!')
                print(medicamentos_seleccionados)
                Consulta_Receta.objects.filter(consulta=consulta).delete()  # Eliminar recetas anteriores
                for medicamento_id in medicamentos_seleccionados:
                    medicamento = Medicamento.objects.get(pk=medicamento_id)
                    via = request.POST.get(f'via_{medicamento.id}')
                    dosis = request.POST.get(f'dosis_{medicamento.id}')
                    frecuencia = request.POST.get(f'frecuencia_{medicamento.id}')
                    duracion = request.POST.get(f'duracion_{medicamento.id}')
                    Consulta_Receta.objects.create(
                        consulta=consulta,
                        medicamento=medicamento,
                        via=via,
                        dosis=dosis,
                        frecuencia=frecuencia,
                        duracion=duracion
                    )
                    print(Consulta_Receta.objects.all())

            # Actualizar exámenes
            examenes_seleccionados = request.POST.getlist('examenes')
            print(examenes_seleccionados)
            Consulta_Examen.objects.filter(consulta=consulta).delete()  # Eliminar exámenes anteriores
            for examen_id in examenes_seleccionados:
                examen = Examen.objects.get(pk=examen_id)
                Consulta_Examen.objects.create(consulta=consulta, examen=examen, estado='solicitado')
                print(Consulta_Examen.objects.all())

            # Actualizar certificado
            certificado = Consulta_Certificado.objects.filter(consulta=consulta).first()
            print('Certificado existente : ', certificado )
            if certificado:
                certificado.lugar_emision = request.POST.get('lugar_emision', '')
                certificado.dirigido_a = request.POST.get('dirigido_a', '')
                certificado.email_empleador = request.POST.get('email_empleador', '')
                certificado.antecedentes = request.POST.get('antecedentes', '')
                certificado.diagnosis = request.POST.get('diagnosis', '')
                certificado.recomendaciones = request.POST.get('recomendaciones', '')
                certificado.inicio = request.POST.get('inicio', None)
                certificado.termino = request.POST.get('termino', None)
                print('Certificado existente y modificado : ', certificado)
            else:
                # Crear un nuevo certificado si este no existe
                certificado = Consulta_Certificado(
                    consulta=consulta,
                    lugar_emision=request.POST.get('lugar_emision', ''),
                    dirigido_a=request.POST.get('dirigido_a', ''),
                    email_empleador=request.POST.get('email_empleador', ''),
                    antecedentes=request.POST.get('antecedentes', ''),
                    diagnosis=request.POST.get('diagnosis', ''),
                    recomendaciones=request.POST.get('recomendaciones', ''),
                    inicio=request.POST.get('inicio', None),
                    termino=request.POST.get('termino', None),
                )

            try:
                certificado.full_clean()  # Validar los datos antes de guardar
                certificado.save()
            except ValidationError as e:
                messages.error(request, f"Error en los datos del certificado: {e}")
                return redirect('A31_Con:consulta_editar', consulta_id=consulta_id)

            messages.success(request, "Consulta actualizada con éxito.")

        except ValueError as e:
            messages.error(request, f"Error: {str(e)}")

    context = {
        'consulta': consulta,
        'examenes': examenes,
        'medicamentos': medicamentos,
        'examenes_seleccionados': consulta.consulta_examenes.values_list('examen__id', flat=True),
        'medicamentos_seleccionados': consulta.consulta_recetas.values_list('medicamento__id', flat=True),
        'certificado': Consulta_Certificado.objects.filter(consulta=consulta).first(),
    }

    return render(request, 'A31_Con/consulta_editar.html', context)


@login_required
def obtener_medicamentos_seleccionados(request):
    medicamentos_seleccionados_ids = request.session.get('medicamentos_seleccionados', [])
    medicamentos_seleccionados = Medicamento.objects.filter(id__in=medicamentos_seleccionados_ids).values('id', 'nombre_gen', 'nombre_com')
    return JsonResponse({'medicamentos': list(medicamentos_seleccionados)})


@login_required
def consulta_detalle(request, consulta_id):
    consulta    = go404(Consulta, pk=consulta_id)
    recetas     = Consulta_Receta.objects.filter(consulta=consulta)
    examenes    = Consulta_Examen.objects.filter(consulta=consulta)
    certificados = Consulta_Certificado.objects.filter(consulta=consulta)
    imagenes    = consulta.consulta_imagenes.all()

    # Verificar si todos los exámenes han sido subidos
    todos_examenes_subidos = all(examen.estado == 'subido' for examen in examenes)

    return render(request, 'A31_Con/consulta_detalle.html', {
        'consulta': consulta,
        'recetas': recetas,
        'examenes': examenes,
        'certificados': certificados,
        'imagenes': imagenes,
        'todos_examenes_subidos': todos_examenes_subidos,
    })

@login_required
def enviar_resultados_al_medico(request, consulta_id):
    consulta    = go404(Consulta, pk=consulta_id)
    paciente    = consulta.hora_medica.paciente.user.get_full_name()
    medico_email = consulta.hora_medica.medico.user.email

    # Enviar email al médico
    send_mail(
        f'Consulta {consulta.id} - Resultados de exámenes subidos',
        f'El paciente {paciente} ha subido todos los resultados de los exámenes solicitados. Por favor, revise los resultados y confirme o modifique el diagnóstico.',
        'ordered.dev.01@gmail.com',
        [medico_email],
        fail_silently=False,
    )

    # Marcar los resultados como enviados
    consulta.resultados_enviados = True
    consulta.save()

    messages.success(request, 'Resultados enviados al médico exitosamente.')
    return redirect('A31_Con:consulta_detalle', consulta_id=consulta_id)


def imprimir_orden_examen(request, consulta_id):
    consulta = go404(Consulta, pk=consulta_id)
    fecha_actual = timezone.localtime(timezone.now()).date()
    fecha_formateada = consulta.hora_medica.f_hra.strftime("%d-%m-%Y")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)

    # Encabezado
    pdf.cell(200, 10, txt=f"Orden de Exámenes", ln=1, align="C", border=1)
    pdf.ln()

    # Información del paciente y médico
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Consulta: {consulta.id}", ln=1)
    pdf.cell(200, 10, txt=f"Fecha: {fecha_formateada}", ln=1)
    pdf.cell(200, 10, txt=f"Paciente: {consulta.hora_medica.paciente.user.first_name} {consulta.hora_medica.paciente.user.last_name}", ln=1)
    pdf.cell(200, 10, txt=f"RUN: {consulta.hora_medica.paciente.user.dni} ", ln=1)
    pdf.cell(200, 10, txt=f"Médico: {consulta.hora_medica.medico.user.first_name} {consulta.hora_medica.medico.user.last_name}", ln=1)
    pdf.cell(200, 10, txt=f"RUN: {consulta.hora_medica.medico.user.dni}", ln=1)
    pdf.ln()

    # Exámenes solicitados
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="Exámenes Solicitados:", ln=1)
    pdf.set_font("Arial", size=12)
    for examen in consulta.consulta_examenes.all():
        pdf.cell(200, 10, txt=f"- {examen.examen.nombre}", ln=1)
    pdf.ln(15)

    # Observaciones
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="Observaciones:", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=consulta.observaciones)  # Multi_cell para observaciones largas


    # Crear carpeta si no existe
    ruta_carpeta = os.path.join(settings.MEDIA_ROOT,"InformesPacientes/OrdExam")  # Nombre de la carpeta
    if not os.path.exists(ruta_carpeta):
        os.makedirs(ruta_carpeta)

    filename=f"Orden-de-Examen-{consulta.id}-{fecha_formateada}-{consulta.hora_medica.paciente.user.last_name}-{consulta.hora_medica.paciente.user.first_name}.pdf"
    filepath=os.path.join(ruta_carpeta,filename)
    pdf.ln()

    pdf.set_font("Helvetica", 'B', size=9)
    pdf.cell(120, 10, txt=f"Archivo: {filename}", ln=1)
    pdf.set_font("Helvetica", 'B', size=12)
    pdf.cell(120, 10, "HumanaSalud, tu salud nuestro compromiso." , 0)
    pdf.output(filepath)

    return HttpResponse(bytes(pdf.output()), content_type="application/pdf")

    context = {
        'fecha_actual': fecha_actual,
        'consulta':consulta,
    }

def imprimir_prescripcion(request, consulta_id):
    consulta = go404(Consulta, pk=consulta_id)
    fecha_actual = timezone.localtime(timezone.now()).date()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)

    # Encabezado
    pdf.cell(200, 10, txt=f"Prescripción Médica", ln=1, align="C", border=3)
    pdf.ln()

    # Información del paciente y médico
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Consulta: {consulta.id}", ln=1)
    fecha_formateada = consulta.hora_medica.f_hra.strftime("%d-%m-%Y")
    pdf.cell(200, 10, txt=f"Fecha: {fecha_formateada}", ln=1)
    pdf.cell(200, 10, txt=f"Paciente: {consulta.hora_medica.paciente.user.first_name} {consulta.hora_medica.paciente.user.last_name}", ln=1)
    pdf.cell(200, 10, txt=f"RUN: {consulta.hora_medica.paciente.user.dni} ", ln=1)
    pdf.cell(200, 10, txt=f"Médico: {consulta.hora_medica.medico.user.first_name} {consulta.hora_medica.medico.user.last_name}", ln=1)
    pdf.cell(200, 10, txt=f"RUN: {consulta.hora_medica.medico.user.dni}", ln=1)
    pdf.ln()

    # Medicamentos prescritos
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="Medicamentos Prescritos:", ln=1)
    pdf.set_font("Arial", size=12)
    for receta in consulta.consulta_recetas.all():
        pdf.cell(200, 10, txt=f"- {receta.medicamento.nombre_gen} ({receta.medicamento.nombre_com})", ln=1)
        pdf.cell(200, 10, txt=f"  Vía: {receta.via}, Dosis: {receta.dosis}, Frecuencia: {receta.frecuencia}, Duración: {receta.duracion}", ln=1)
    pdf.ln(15)

    # Crear carpeta si no existe
    ruta_carpeta = os.path.join(settings.MEDIA_ROOT,"InformesPacientes/Prescripciones")  # Nombre de la carpeta
    if not os.path.exists(ruta_carpeta):
        os.makedirs(ruta_carpeta)

    filename=f"Prescripción-{consulta.id}-{fecha_formateada}-{consulta.hora_medica.paciente.user.last_name}-{consulta.hora_medica.paciente.user.first_name}.pdf"
    filepath=os.path.join(ruta_carpeta,filename)
    pdf.ln()

    pdf.set_font("Helvetica", 'B', size=9)
    pdf.cell(120, 10, txt=f"Archivo: {filename}", ln=1)
    pdf.set_font("Helvetica", 'B', size=12)
    pdf.cell(120, 10, "HumanaSalud, tu salud nuestro compromiso." , 0)
    pdf.output(filepath)

    return HttpResponse(bytes(pdf.output()), content_type="application/pdf")

    context = {
        'fecha_actual': fecha_actual,
        'consulta':consulta,
    }

def imprimir_certificado(request, consulta_id):
    consulta = go404(Consulta, pk=consulta_id)
    fecha_actual = timezone.localtime(timezone.now()).date()
    fecha_formateada = consulta.hora_medica.f_hra.strftime("%d-%m-%Y")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)

    # Encabezado
    pdf.cell(200, 10, txt="Certificado Médico", ln=1, align="C", border=1)

    # Información del paciente y médico
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Consulta: {consulta.id}", ln=1)
    pdf.cell(200, 10, txt=f"Fecha: {fecha_formateada}", ln=1)
    pdf.cell(200, 10, txt=f"Paciente: {consulta.hora_medica.paciente.user.first_name} {consulta.hora_medica.paciente.user.last_name}", ln=1)
    pdf.cell(200, 10, txt=f"RUN: {consulta.hora_medica.paciente.user.dni} ", ln=1)
    pdf.cell(200, 10, txt=f"Médico: {consulta.hora_medica.medico.user.first_name} {consulta.hora_medica.medico.user.last_name}", ln=1)
    pdf.cell(200, 10, txt=f"RUN: {consulta.hora_medica.medico.user.dni}", ln=1)
    pdf.ln()

    # Certificado
    certificado = consulta.consulta_certificados.first()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="Certificado:", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Lugar de Emisión: {certificado.lugar_emision}", ln=1)
    pdf.cell(200, 10, txt=f"Dirigido a: {certificado.dirigido_a}", ln=1)
    pdf.cell(200, 10, txt=f"Antecedentes: {certificado.antecedentes}", ln=1)
    pdf.cell(200, 10, txt=f"Diagnóstico: {certificado.diagnosis}", ln=1)
    pdf.cell(200, 10, txt=f"Recomendaciones: {certificado.recomendaciones}", ln=1)
    pdf.cell(200, 10, txt=f"Inicio: {certificado.inicio}", ln=1)
    pdf.cell(200, 10, txt=f"Término: {certificado.termino}", ln=1)
    pdf.ln(15)

    # Crear carpeta si no existe
    ruta_carpeta = os.path.join(settings.MEDIA_ROOT, "InformesPacientes/Certificados")  # Nombre de la carpeta
    if not os.path.exists(ruta_carpeta):
        os.makedirs(ruta_carpeta)

    # Construcción de la ruta del archivo PDF
    filename=f"Certificado-{consulta.id}-{fecha_formateada}-{consulta.hora_medica.paciente.user.last_name}-{consulta.hora_medica.paciente.user.first_name}.pdf"
    filepath = os.path.join(ruta_carpeta, filename)
    pdf.ln()

    pdf.set_font("Helvetica", 'B', size=9)
    pdf.cell(120, 10, txt=f"Archivo: {filename}", ln=1)
    pdf.set_font("Helvetica", 'B', size=12)
    pdf.cell(120, 10, "HumanaSalud, tu salud nuestro compromiso." , 0)
    pdf.output(filepath)

    return HttpResponse(bytes(pdf.output()), content_type="application/pdf")



def enviar_email_certificado(request, consulta_id):
    consulta = go404(Consulta, pk=consulta_id)
    certificado = consulta.consulta_certificados.first()

    if certificado is None:
        return JsonResponse({'success': False, 'error': 'Certificado no encontrado'})

    try:
        email_paciente = consulta.hora_medica.paciente.user.email
        email_empleador = certificado.email_empleador

        # Construcción de la ruta del archivo PDF
        fecha_formateada = consulta.hora_medica.f_hra.strftime("%d-%m-%Y")
        filename = f"Certificado-{consulta.id}-{fecha_formateada}-{consulta.hora_medica.paciente.user.last_name}-{consulta.hora_medica.paciente.user.first_name}.pdf"
        filepath = os.path.join(settings.MEDIA_ROOT, "InformesPacientes/Certificados", filename)

        # Verificar si el archivo existe
        if not os.path.exists(filepath):
            logger.error(f"Archivo PDF no encontrado: {filepath}")
            return JsonResponse({'success': False, 'error': 'Archivo PDF no encontrado'})

        # # Leer el archivo PDF y convertirlo a Base64
        # with open(filepath, 'rb') as f:
        #     file_data = f.read()
        #     file_base64 = base64.b64encode(file_data).decode('utf-8')

        # Construir la lista de destinatarios
        destinatarios = [email_paciente]
        if email_empleador:
            destinatarios.append(email_empleador)

        # Verificar los destinatarios
        logger.debug(f"Destinatarios: {destinatarios}")

        # email = EmailMessage(
        #         'Certificado Médico',
        #         'Estimado Paciente, en forma adjunta encontrará su certificado médico.',
        #         'ordered.dev.01@gmail.com',
        #         destinatarios
        #         )


        # Construir la URL del archivo PDF
        file_url = f"{settings.MEDIA_URL}InformesPacientes/Certificados/{filename}"
        # Verificar la URL
        print(f"URL del archivo PDF: {file_url}") #Agregado.

        # Crear el mensaje de correo electrónico HTML
        subject = 'Certificado Médico'
        text_content = f'Estimado(a) Paciente,\n\nAdjunto encontrará su certificado médico. Puede descargarlo desde el siguiente enlace:\n\n{file_url}'
        html_content = f'<p>Estimado(a) Paciente,</p><p>Adjunto encontrará su certificado médico. Puede descargarlo desde el siguiente enlace: <a href="{file_url}">Descargar Certificado</a></p>'

        msg = EmailMultiAlternatives(subject, text_content, 'ordered.dev.01@gmail.com', destinatarios)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        # email.attach_file('Certificado.pdf', base64.b64decode(file_base64), 'application/pdf')
        # email.attach_file(filepath)
        # email.send()

        logger.info(f"Certificado enviado exitosamente a {email_paciente}")
        return JsonResponse({'success': True})

    except FileNotFoundError:
        logger.error(f"Error al encontrar el archivo PDF: {e}")
        return JsonResponse({'success': False, 'error': 'Archivo PDF no encontrado'})
    except Exception as e:
        logger.exception(f"Error inesperado al enviar el correo: {e}")
        return JsonResponse({'success': False, 'error': str(e)})



@login_required
def consulta_informes(request):
    user = request.user
    pacientes = []

    if user.is_superuser or user.groups.filter(name__in=['Jefe de plataforma', 'Recepcionista']).exists():
        # Superusuario, jefe de plataforma o recepcionista: ven todos los pacientes
        pacientes = Paciente.objects.all()
    elif user.groups.filter(name='Médico').exists():
        # Médico: ve solo sus pacientes
        medico = user.medico
        pacientes = Paciente.objects.filter(hora_medica__medico=medico).distinct()
    elif user.groups.filter(name='Paciente').exists():
        # Paciente: ve solo sus consultas
        pacientes = Paciente.objects.filter(user=user)

    return render(request, 'A31_Con/consulta_informes.html', {'pacientes': pacientes})



@login_required
def informe_historico(request, paciente_id):
    user = go404(CustomUser, pk=paciente_id)
    paciente = go404(Paciente, user=user.id)
    consultas = Consulta.objects.filter(hora_medica__paciente=paciente).order_by('hora_medica__f_hra')

    # CASO 1 : Verificar si hay consultas
    if not consultas:
        return render(request, 'A31_Con/informe_historico.html', {
            'paciente': paciente,
            'mensaje': 'El paciente no tiene consultas registradas.'
        })

    # Preparar datos para gráficos
    fechas = [consulta.hora_medica.f_hra for consulta in consultas]
    if isinstance(fechas[0], str):
        fechas = [datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S%z') for date_str in fechas]

    p_sistolicas = [int(consulta.p_sistolica) for consulta in consultas]
    p_diastolicas = [int(consulta.p_diastolica) for consulta in consultas]
    imcs = [float(consulta.imc) if consulta.imc is not None else 0.0 for consulta in consultas]
    pesos = [float(consulta.peso) for consulta in consultas]

    # CASO 2 : Solo una consulta
    if len(consultas) == 1:
        # Creación de la figura plt.figure().
        plt.figure(figsize=(12, 6))
        # Trazado de los datos plt.plot().
        plt.plot(fechas, p_sistolicas, label='Presión Sistólica', marker='o', color='C0')
        plt.plot(fechas, p_diastolicas, label='Presión Diastólica', marker='o', color='C1')
        plt.plot(fechas, pesos, label='Peso (Kg)', marker='o', color='C2')
        plt.plot(fechas, imcs, label='IMC', marker='o', color='C3')
        # Configuración de los ejes, títulos y leyendas.
        plt.xlabel('Fecha')
        plt.ylabel('Valores')
        plt.title('Presiones, pesos e IMC en el Tiempo (Sin predicción)')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        # Guardar gráfico en búfer plt.savefig(), Codificación del búfer en base64 y
        # Creación de la URI para la imagen.
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        string = base64.b64encode(buf.read())
        uri = urllib.parse.quote(string)
        return render(request, 'A31_Con/informe_historico.html', {
            'paciente': paciente,
            'grafico_presiones': uri,
            'mensaje': 'El paciente tiene una sola consulta registrada.',
        })

    # CASO 3 : Más de una consulta

    # Calcular tiempo futuro de predicción (25% del tiempo total)
    delta_tiempo = fechas[-1] - fechas[0]
    tiempo_futuro_prediccion = fechas[-1] + delta_tiempo * 0.25

    f_p_sistolica = interp1d([f.timestamp() for f in fechas], p_sistolicas, fill_value="extrapolate")
    f_p_diastolica = interp1d([f.timestamp() for f in fechas], p_diastolicas, fill_value="extrapolate")
    f_peso = interp1d([f.timestamp() for f in fechas], pesos, fill_value="extrapolate")
    f_imc = interp1d([f.timestamp() for f in fechas], imcs, fill_value="extrapolate")

    prediccion_p_sistolica = float(f_p_sistolica(tiempo_futuro_prediccion.timestamp()))
    prediccion_p_diastolica = float(f_p_diastolica(tiempo_futuro_prediccion.timestamp()))
    prediccion_peso = float(f_peso(tiempo_futuro_prediccion.timestamp()))
    prediccion_imc = float(f_imc(tiempo_futuro_prediccion.timestamp()))

    fechas_prediccion = [tiempo_futuro_prediccion]
    p_sistolicas_prediccion = [prediccion_p_sistolica]
    p_diastolicas_prediccion = [prediccion_p_diastolica]
    pesos_prediccion = [prediccion_peso]
    imcs_prediccion = [prediccion_imc]

    fechas = pd.to_datetime(fechas)
    fechas_prediccion = pd.to_datetime(fechas_prediccion)

    fechas_reales = fechas
    p_sistolicas_reales = p_sistolicas
    p_diastolicas_reales = p_diastolicas
    pesos_reales = pesos
    imcs_reales = imcs

    plt.figure(figsize=(12, 6))
    plt.plot(fechas_reales, p_sistolicas_reales, label='Presión Sistólica', marker='o', color='C0', linestyle='-')
    plt.plot(fechas_reales, p_diastolicas_reales, label='Presión Diastólica', marker='o', color='C1', linestyle='-')
    plt.plot(fechas_reales, pesos_reales, label='Peso (Kg)', marker='o', color='C2', linestyle='-')
    plt.plot(fechas_reales, imcs_reales, label='IMC', marker='o', color='C3', linestyle='-')

    plt.plot(fechas_prediccion, p_sistolicas_prediccion, marker='x', color='C0', linestyle='--', label='Predicción Sistólica')
    plt.plot(fechas_prediccion, p_diastolicas_prediccion, marker='x', color='C1', linestyle='--', label='Predicción Diastólica')
    plt.plot(fechas_prediccion, pesos_prediccion, marker='x', color='C2', linestyle='--', label='Predicción Peso (Kg)')
    plt.plot(fechas_prediccion, imcs_prediccion, marker='x', color='C3', linestyle='--', label='Predicción IMC')

    for i, fecha in enumerate(fechas_reales):
        plt.text(fecha, p_sistolicas_reales[i], str(p_sistolicas_reales[i]), fontsize=8, ha='center', va='bottom')
        plt.text(fecha, p_diastolicas_reales[i], str(p_diastolicas_reales[i]), fontsize=8, ha='center', va='bottom')
        plt.text(fecha, pesos_reales[i], str(pesos_reales[i]), fontsize=8, ha='center', va='bottom')
        plt.text(fecha, imcs_reales[i], str(imcs_reales[i]), fontsize=8, ha='center', va='bottom')

    for i, fecha in enumerate(fechas_prediccion):
        plt.text(fecha, p_sistolicas_prediccion[i], str(p_sistolicas_prediccion[i]), fontsize=8, ha='center', va='bottom')
        plt.text(fecha, p_diastolicas_prediccion[i], str(p_diastolicas_prediccion[i]), fontsize=8, ha='center', va='bottom')
        plt.text(fecha, pesos_prediccion[i], str(pesos_prediccion[i]), fontsize=8, ha='center', va='bottom')
        plt.text(fecha, imcs_prediccion[i], str(imcs_prediccion[i]), fontsize=8, ha='center', va='bottom')

    plt.xlabel('Fecha')
    plt.ylabel('Valores')
    plt.title('Presiones, pesos e IMC en el Tiempo')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    grafico_presiones = uri

    # Comentarios sobre la predicción
    comentarios = "Comentarios sobre la predicción:\n"
    if prediccion_p_sistolica > 140 or prediccion_p_diastolica > 90:
        comentarios += "- La presión arterial predicha es elevada. Se recomienda hacer seguimiento cada 30 días. \n"
    if prediccion_imc > 30:
        comentarios += "- El IMC predicho indica obesidad. Se recomienda adoptar un estilo de vida saludable y monitorear cada 30 días.\n"
    if prediccion_peso > 100:
        comentarios += "- El peso predicho es elevado. Se recomienda una dieta balanceada y ejercicio regular.\n"
    if prediccion_peso < 50:
        comentarios += "- El peso predicho es bajo. Se recomienda una evaluación nutricional.\n"

    # Últimos diagnósticos y prescripciones
    ultimos_diagnosticos = consultas.order_by('-hora_medica__f_hra')[:3]

    # Exámenes pendientes
    examenes_pendientes = Consulta_Examen.objects.filter(consulta__hora_medica__paciente=paciente, estado='solicitado')

    return render(request, 'A31_Con/informe_historico.html',locals())

def consultas_resumen(request, paciente_id):
    user = go404(CustomUser, pk=paciente_id)
    paciente = go404(Paciente, user=user.id)
    consultas = Consulta.objects.filter(hora_medica__paciente=paciente).order_by('-hora_medica__f_hra')
    return render(request, 'A31_Con/consultas_resumen.html', {'paciente': paciente, 'consultas': consultas})

def detalle_consulta(request, consulta_id):
    consulta = go404(Consulta, id=consulta_id)
    recetas = Consulta_Receta.objects.filter(consulta=consulta)
    examenes = Consulta_Examen.objects.filter(consulta=consulta)
    certificados = Consulta_Certificado.objects.filter(consulta=consulta)
    imagenes = consulta.consulta_imagenes.all()
    return render(request, 'A31_Con/detalle_consulta.html', {
        'consulta': consulta,
        'recetas': recetas,
        'examenes': examenes,
        'certificados': certificados,
        'imagenes': imagenes,
    })


@login_required
def subir_resultado_examen(request, examen_id):
    examen = Consulta_Examen.objects.get(id=examen_id)
    consulta = examen.consulta
    medico = consulta.hora_medica.medico

    if request.method == 'POST' and request.FILES['archivo']:
        archivo = request.FILES['archivo']
        fs = FileSystemStorage()
        filename = fs.save(archivo.name, archivo)
        examen.archivo = filename
        examen.estado = 'subido'
        examen.save()

        # Notificar al médico
        send_mail(
            'Nuevo resultado de examen subido',
            f'El paciente {consulta.hora_medica.paciente.user.get_full_name()} ha subido un nuevo resultado de examen.',
            'noreply@humanasalud.com',#
            [medico.user.email],
            fail_silently=False,
        )

        return redirect('A31_Con:consulta_detalle', consulta_id=consulta.id)

    return render(request, 'A31_Con/subir_resultado_examen.html', {'examen': examen})


@login_required
def bajar_resultado_examen(request, examen_id):
    examen = go404(Consulta_Examen, pk=examen_id)  # Filtrar por examen_id
    consulta = examen.consulta
    medico = consulta.hora_medica.medico
    examen.archivo = None
    examen.estado = 'solicitado'
    examen.save()
    # Redirigir a la vista de detalle de la consulta o a donde sea necesario
    return redirect('A31_Con:consulta_detalle', consulta_id=consulta.id) # Reemplazar 'consulta_detalle' con el nombre de tu URL
