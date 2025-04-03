from A20_Hrs.models import HoraMedica
from A31_Con.models import *
from .forms import *
from .utils import enviar_email_clave_provisoria,generar_clave_provisoria
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from allauth.account.views import ConfirmEmailView
from django.forms import ValidationError
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required #Para que solo los staff puedan crear usuarios
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash #Para actualizar la sesión despues de cambiar la contraseña
from django.contrib.auth import get_backends
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db import DatabaseError, transaction, IntegrityError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode,  urlsafe_base64_decode

from icecream import ic
from random import choices
from string import ascii_lowercase, digits

import logging
import random
import string
import datetime as dt



#* ########################################
#* #####          LOGEOS              #####
#* ########################################
logger = logging.getLogger(__name__)

@login_required
def redireccion_despues_login(request):
    user = request.user

    if hasattr(user, 'paciente'): # Si el usuario es un paciente y no ha completado su perfil, redirigirlo a la página de completar perfil de paciente (completar_perfil_paciente).
        return redirect('completar_perfil_paciente')
    elif hasattr(user, 'jefeplataforma'):
        return redirect('completar_perfil_jefe_plataforma')
    elif hasattr(user, 'medico'):
        return redirect('completar_perfil_medico')
    elif hasattr(user, 'recepcionista'):
        return redirect('completar_perfil_recepcionista')
    else:
        if user.is_superuser:
            rol = 'Superusuario'
        elif user.groups.filter(name='Jefes de Plataforma').exists():
            rol = 'Jefe de Plataforma'
        elif user.groups.filter(name='Recepcionistas').exists():
            rol = 'Recepcionista'
        elif request.user.groups.filter(name__in=['Medicos']).exists():
            rol = 'Médico'
        elif user.groups.filter(name='Pacientes').exists():
            rol = 'Paciente'
        else:
            rol = 'Sin rol asignado'
        return render(request,'home.html', locals())

@login_required
def home(request):
    user = request.user
    if user.is_superuser:
        rol = 'Superusuario'
    elif user.groups.filter(name__in=['Jefes de Plataforma']).exists():
        rol = 'Jefe de Plataforma'
    elif user.groups.filter(name='Recepcionistas').exists():
        rol = 'Recepcionista'
    elif user.groups.filter(name__in=['Medicos']).exists():
        rol = 'Médico'
    elif user.groups.filter(name='Pacientes').exists():
        rol = 'Paciente'
    else:
        rol = 'Sin rol asignado'
    ic('###############   ',rol)
    return render(request, 'home.html', locals())

def seleccionar_tipo_registro(request):
    if request.method == 'POST':
        form = SeleccionarTipoRegistroForm(request.POST)
        if form.is_valid():
            tipo_usuario = form.cleaned_data.get('tipo_usuario')
            if tipo_usuario == 'paciente':
                return redirect('registro_paciente')
            elif tipo_usuario == 'jefeplataforma':
                return redirect('registro_jefe_plataforma')
        else:
            form = SeleccionarTipoRegistroForm()
        return render(request, 'A10_Usu/seleccionar_tipo_registro.html', {'form': form})



#* ########################################
#* #####         PARÁMETROS           #####
#* ########################################
@login_required
def vista_parametros(request):
    if request.user.groups.filter(name__in=['Jefes de Plataforma',]).exists() or request.user.is_superuser:
        return render(request, 'A10_Usu/vista_parametros.html', locals())
    else:
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('home')

@login_required
def registro_genero(request):
    generos = Genero.objects.all()
    if request.method == 'POST':
        form = GeneroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = GeneroForm()
    return render(request, 'A10_Usu/registro_genero.html', {'form': form,'generos':generos})

@login_required
def registro_sistema_salud(request):
    sis = SistemaSalud.objects.all()

    if request.method == 'POST':
        form = SistemaSaludForm(request.POST)
        if form.is_valid():
            ic(request.POST.get('name'))
            form.save()
            return redirect('home')
    else:
        form = SistemaSaludForm()
    return render(request, 'A10_Usu/registro_sistema_salud.html', {'form': form, 'sistemas': sis})

@login_required
def registro_especialidad(request):
    especialidades=Especialidad.objects.all()
    if request.method == 'POST':
        form = EspecialidadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = EspecialidadForm()
    return render(request, 'A10_Usu/registro_especialidad.html', {'form': form,'especialidades':especialidades})

@login_required
def registroExamen(request):
    examenes=Examen.objects.all()
    if request.method == 'POST':
        form = ExamenForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Examen registrado exitosamente.")
            return redirect('A10_Usu:registroExamen')
        else:
            messages.error(request, "Error al registrar el examen. Verifica los campos.")
    else:
        form = ExamenForm()
    return render(request, 'A10_Usu/registroExamen.html', locals())

@login_required
def registroMedicamento(request):
    medicamentos=Medicamento.objects.all()
    if request.method == 'POST':
        form = MedicamentoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('A10_Usu:registroMedicamento')
    else:
        form = MedicamentoForm()
    return render(request, 'A10_Usu/registroMedicamento.html', locals())

@login_required
def medicamentoVer(request, pk):
    medicamento = get_object_or_404(Medicamento, pk=pk)
    return render(request, 'A10_Usu/medicamentoVer.html', {'medicamento': medicamento})

@login_required
def medicamentoEditar(request, pk):
    medicamento = get_object_or_404(Medicamento, pk=pk)
    if request.method == 'POST':
        form = MedicamentoForm(request.POST, request.FILES, instance=medicamento)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = MedicamentoForm(instance=medicamento)
    return render(request, 'A10_Usu/medicamentoEditar.html', {'form': form, 'medicamento': medicamento})



#* ##########     REGISTROS     ###########
#* ########################################
@login_required
def registro_usuario(request):
    if request.method == 'POST':
        form = GenericSignupForm(request.POST, user=request.user)
        if form.is_valid():
            role = form.cleaned_data['role']
            email = form.cleaned_data['email']
            password = ''.join(choices(ascii_lowercase + digits, k=10))
            # user = CustomUser.objects.create_user(
            #     username=email,
            #     email=email,
            #     password=password,
            #     is_active=False
            # )
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={'username': email, 'password': password, 'is_active': False}
            )
            if not created:
                user.set_password(password)
                user.is_active = False
                user.save()

            logger.info(f"User created: {user.email} (ID: {user.id})")

            # Crear el grupo y asignar permisos
            if role == 'paciente' and (request.user.is_superuser or request.user.has_perm('A10_Usu.add_paciente')):
                group, created = Group.objects.get_or_create(name='Pacientes')
                if created:
                    home_paciente_permission = Permission.objects.get(codename='Home_Paciente')
                    group.permissions.add(home_paciente_permission)
                Paciente.objects.get_or_create(user=user)

            elif role == 'jefe_plataforma' and request.user.has_perm('A10_Usu.add_jefeplataforma'):
                group, created = Group.objects.get_or_create(name='Jefes de Plataforma')
                if created:
                    add_paciente_permission = Permission.objects.get(codename='add_paciente')
                    group.permissions.add(add_paciente_permission)

                    add_recepcionista_permission = Permission.objects.get(codename='add_recepcionista')
                    group.permissions.add(add_recepcionista_permission)

                    add_medico_permission = Permission.objects.get(codename='add_medico')
                    group.permissions.add(add_medico_permission)

                JefePlataforma.objects.get_or_create(user=user)

            elif role == 'recepcionista' and request.user.has_perm('A10_Usu.add_recepcionista'):
                group, created = Group.objects.get_or_create(name='Recepcionistas')
                if created:
                    add_paciente_permission = Permission.objects.get(codename='add_paciente')
                    group.permissions.add(add_paciente_permission)
                Recepcionista.objects.get_or_create(user=user)

            elif role == 'medico' and request.user.has_perm('A10_Usu.add_medico'):
                group, created = Group.objects.get_or_create(name='Medicos')
                if created:
                    home_medico_permission = Permission.objects.get(codename='Home_Medico')
                    group.permissions.add(home_medico_permission)
                Medico.objects.get_or_create(user=user)

            else:
                messages.error(request, 'No tienes permiso para crear este tipo de usuario.')
                user.delete()
                return redirect('A10_Usu:registro_usuario')

            # Asignar el usuario al grupo
            user.groups.add(group)

            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            verification_url = request.build_absolute_uri(reverse('A10_Usu:verificar_cuenta', kwargs={'uidb64': uidb64, 'token': token}))

            subject = 'Bienvenido a HumanaSalud - Activa tu cuenta'
            context = {'user': user, 'verification_url': verification_url, 'password': password}
            html_message = render_to_string('A10_Usu/verificar_cuenta.html', context)
            plain_message = strip_tags(html_message)
            from_email = 'ordered.dev.01@gmail.com'
            to = user.email
            send_mail(subject, plain_message, from_email, [to], html_message=html_message)

            messages.success(request, f'Hemos enviado un correo electrónico a {user.email}. En este encontrarás un link que te permitirá activar tu cuenta y completar tu perfil.')
            return redirect('A10_Usu:mensaje_verificacion_enviado')
    else:
        form = GenericSignupForm(user=request.user)
    return render(request, 'A10_Usu/registro_usuario.html', {'form': form})


def registro_paciente(request):
    if request.method == 'POST':
        form = PacienteSignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = ''.join(choices(ascii_lowercase + digits, k=10))
            # user = CustomUser.objects.create_user(
            #     username=email,
            #     email=email,
            #     password=password,
            #     is_active=False
            # )
            #
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={'username': email, 'password': password, 'is_active': False}
            )
            if not created:
                user.set_password(password)
                user.is_active = False
                user.save()
            logger.info(f"User created or updated: {user.email} (ID: {user.id})")

            group, created = Group.objects.get_or_create(name='Pacientes')
            if created:
                home_paciente_permission = Permission.objects.get(codename='Home_Paciente')
                group.permissions.add(home_paciente_permission)

            user.groups.add(group)

            paciente = Paciente.objects.create(user=user)

            ic(user)
            ic(paciente)

            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            verification_url = request.build_absolute_uri(reverse('A10_Usu:verificar_cuenta', kwargs={'uidb64': uidb64, 'token': token}))

            subject = 'Bienvenido a HumanaSalud - Activa tu cuenta'
            context = {'user': user, 'verification_url': verification_url, 'password': password}
            html_message = render_to_string('A10_Usu/verificar_cuenta.html', context)
            plain_message = strip_tags(html_message)
            from_email = 'ordered.dev.01@gmail.com'
            to = user.email
            send_mail(subject, plain_message, from_email, [to], html_message=html_message)

            messages.success(request, f'Hemos enviado un correo electrónico a {user.email}. En este encontrarás un link que te permitirá activar tu cuenta y completar tu perfil.')
            return redirect('A10_Usu:mensaje_verificacion_enviado')
    else:
        form = PacienteSignupForm()
    return render(request, 'A10_Usu/registro_paciente.html', {'form': form})



#* #####          Perfiles            #####
#* ########################################
@login_required
def mensaje_verificacion_enviado(request): #Vista para mostrar el mensaje de verificacion enviado
    return render(request, 'A10_Usu/mensaje_verificacion_enviado.html')

@login_required
def verificar_cuenta(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        logger.info(f"Decoded UID: {uid}")
        user = CustomUser.objects.get(pk=uid)
        logger.info(f"User found: {user.email} (ID: {user.id})")
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            backend = get_backends()[0]  # Obtén el primer backend de autenticación configurado
            user.backend = f'{backend.__module__}.{backend.__class__.__name__}'
            login(request, user, backend=user.backend)
            messages.success(request, '¡Tu cuenta ha sido activada! Por favor, completa tu perfil.')

            # Redirigir según el rol del usuario
            if hasattr(user, 'paciente_profile'):
                return redirect('A10_Usu:completar_perfil_paciente', paciente_id=user.id)
            elif hasattr(user, 'jefeplataforma_profile'):
                return redirect('A10_Usu:completar_perfil_jefe_plataforma', jefe_plataforma_id=user.id)
            elif hasattr(user, 'recepcionista_profile'):
                return redirect('A10_Usu:completar_perfil_recepcionista', recepcionista_id=user.id)
            elif hasattr(user, 'medico_profile'):
                return redirect('A10_Usu:completar_perfil_medico', medico_id=user.id)
            else:
                messages.error(request, 'No se pudo determinar el rol del usuario.')
                return redirect('account_login')
        else:
            messages.error(request, 'El enlace de activación es inválido o ha expirado.')
            return redirect('account_login')
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist) as e:
        logger.error(f"Error during account activation: {e}")
        messages.error(request, 'Ocurrió un error al activar tu cuenta. Por favor, intenta nuevamente más tarde.')
        return redirect('account_login')

@login_required
def actualizar_usuario(user, form):
    user.first_name = form.cleaned_data['first_name']
    user.last_name = form.cleaned_data['last_name']
    user.dni = form.cleaned_data['dni']
    user.f_nacim = form.cleaned_data['f_nacim']
    user.imagen = form.cleaned_data['imagen']
    user.genero = form.cleaned_data['genero']
    user.tel_pers = form.cleaned_data['tel_pers']
    user.name_emerg = form.cleaned_data['name_emerg']
    user.tel_emerg = form.cleaned_data['tel_emerg']
    if form.cleaned_data['new_password1']:
        user.set_password(form.cleaned_data['new_password1'])
    user.save()


@login_required
def completar_perfil_paciente(request, paciente_id):
    user = get_object_or_404(CustomUser, pk=paciente_id)
    paciente = get_object_or_404(Paciente, user=user)
    if paciente.perfil_completo:
        return redirect('home')

    if request.method == 'POST':
        form = PacienteProfileForm(request.POST, request.FILES, instance=paciente)
        if form.is_valid():
            paciente = form.save(commit=False)
            actualizar_usuario(user, form)
            paciente.perfil_completo = True
            paciente.save()
            messages.success(request, 'Perfil completado exitosamente.')
            return redirect('home')
    else:
        form = PacienteProfileForm(instance=paciente, initial={'first_name': user.first_name, 'last_name': user.last_name})
    return render(request, 'A10_Usu/completar_perfil_paciente.html', {'form': form})

@login_required
def completar_perfil_jefe_plataforma(request, jefe_plataforma_id):
    user = get_object_or_404(CustomUser, pk=jefe_plataforma_id)
    jefe_plataforma = get_object_or_404(JefePlataforma, user=user)
    if jefe_plataforma.perfil_completo:
        return redirect('home')

    if request.method == 'POST':
        form = JefePlataformaProfileForm(request.POST, request.FILES, instance=jefe_plataforma)
        if form.is_valid():
            jefe_plataforma = form.save(commit=False)
            actualizar_usuario(user, form)
            jefe_plataforma.perfil_completo = True
            jefe_plataforma.save()
            messages.success(request, 'Perfil completado exitosamente.')
            return redirect('home')
    else:
        form = JefePlataformaProfileForm(instance=jefe_plataforma, initial={'first_name': user.first_name, 'last_name': user.last_name})
    return render(request, 'A10_Usu/completar_perfil_jefe_plataforma.html', {'form': form})

@login_required
def completar_perfil_recepcionista(request, recepcionista_id):
    user = get_object_or_404(CustomUser, pk=recepcionista_id)
    recepcionista = get_object_or_404(Recepcionista, user=user)
    if recepcionista.perfil_completo:
        return redirect('home')

    if request.method == 'POST':
        form = RecepcionistaProfileForm(request.POST, request.FILES, instance=recepcionista)
        if form.is_valid():
            recepcionista = form.save(commit=False)
            actualizar_usuario(user, form)
            recepcionista.perfil_completo = True
            recepcionista.save()
            messages.success(request, 'Perfil completado exitosamente.')
            return redirect('home')
    else:
        form = RecepcionistaProfileForm(instance=recepcionista, initial={'first_name': user.first_name, 'last_name': user.last_name})
    return render(request, 'A10_Usu/completar_perfil_recepcionista.html', {'form': form})

@login_required
def completar_perfil_medico(request, medico_id):
    user = get_object_or_404(CustomUser, pk=medico_id)
    medico = get_object_or_404(Medico, user=user)
    if medico.perfil_completo:
        return redirect('home')

    if request.method == 'POST':
        form = MedicoProfileForm(request.POST, request.FILES, instance=medico)
        if form.is_valid():
            medico = form.save(commit=False)
            actualizar_usuario(user, form)
            medico.perfil_completo = True
            medico.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Perfil completado exitosamente.')
            return redirect('home')
    else:
        form = MedicoProfileForm(instance=medico, initial={'first_name': user.first_name, 'last_name': user.last_name})
    return render(request, 'A10_Usu/completar_perfil_medico.html', {'form': form})



#* #####           Listar             #####
#* ########################################
@login_required
def usuarios(request): #Ok
    if request.user.is_superuser or request.user.groups.filter(name__in=['Jefes de Plataforma']).exists():
        rol = request.GET.get('rol')
        apellido = request.GET.get('apellido')
        ic(rol, apellido)

        pacientes = None
        usuarios = None

        if rol == 'Pacientes' and apellido:
            usuarios = CustomUser.objects.filter(groups__name=rol, is_active=True, last_name__icontains=apellido)
        elif rol == 'Pacientes' and not apellido:
            usuarios = CustomUser.objects.filter(groups__name=rol, is_active=True)
            apellido =''
        elif rol in ['Medicos', 'Jefes de Plataforma', 'Recepcionistas'] and not apellido:
            usuarios = CustomUser.objects.filter(groups__name=rol, is_active=True)
            apellido =''
        elif rol in ['Medicos', 'Jefes de Plataforma', 'Recepcionistas'] and apellido:
            usuarios = CustomUser.objects.filter(groups__name=rol, is_active=True, last_name__icontains=apellido)
        elif rol == 'Todos' or not rol and not apellido:
            usuarios = CustomUser.objects.filter(is_active=True)
            apellido =''
        elif rol == 'Todos' or not rol and apellido:
            usuarios = CustomUser.objects.filter(is_active=True).filter(Q(last_name__icontains=apellido)|Q(first_name__icontains=apellido))

        roles = Group.objects.all().exclude(name='Super Usuarios')
        messages.info(request, "Acceso permitido")
    else:
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('accounts:redireccion_despues_login')

    # Combinar pacientes y usuarios en una sola lista
    combined_list = []
    if pacientes:
        for paciente in pacientes:
            combined_list.append({
                'first_name': paciente.user.first_name,
                'last_name': paciente.user.last_name,
                'email': paciente.user.email,
                'role': 'Paciente',
                'id': paciente.user.id,
                'is_paciente': True
            })
    if usuarios:
        for user in usuarios:
            if user.is_superuser == False: # No mostrar a los superusuarios en la lista
                combined_list.append({
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'role': user.groups.first().name if user.groups.exists() else 'Super Usuario', # Obtener el primer grupo asignado al usuario o 'Super Usuario' si no tiene ninguno.
                'id': user.id,
                'is_paciente': user.groups.filter(name='Pacientes').exists()
                })
    ic(combined_list)

    # Eliminar duplicados basados en el correo electrónico
    seen_emails = set() # Un conjunto es una colección no ordenada de elementos únicos.
    ic(seen_emails)

    unique_list = []
    for user in combined_list:
        if user['email'] not in seen_emails:
            seen_emails.add(user['email'])
            unique_list.append(user)
    ic(unique_list)

    return render(request, 'A10_Usu/usuarios.html', {
        'usuarios': unique_list,
        'roles': roles,
        'selected_rol': rol,
        'apellido': apellido,
    })

@login_required
def listar_pacientes(request):
    if request.user.is_superuser:
        try:
            pacientes = Paciente.objects.filter(perfil_completo=True)
            messages.info(request, "Accediendo a la lista de pacientes.")
        except Paciente.DoesNotExist:
            pacientes = None
            messages.error(request, "No se encontraron pacientes.")
    elif request.user.groups.filter(name__in=['Medicos']).exists():
        try:
            medico = request.user.medico_profile  # Obtén el perfil de médico del usuario
            pacientes_atendidos = Paciente.objects.filter(
            paciente_horas__hora_medica_consultas__hora_medica__medico=medico
        ).distinct()
            # pacientes_atendidos = Paciente.objects.filter(paciente_fichas__medico=medico).distinct()
            horas_futuras = HoraMedica.objects.filter(medico=medico, f_hra__gte=dt.datetime.now())
            messages.info(request, "Accediendo a la lista de pacientes.")
        except Paciente.DoesNotExist:
            pacientes = None
            messages.error(request, "No se encontraron pacientes.")
    elif request.user.groups.filter(name__in=['Recepcionistas']).exists():
        try:
            pacientes = Paciente.objects.filter(perfil_completo=True)
            messages.info(request, "Accediendo a la lista de pacientes.")
        except Paciente.DoesNotExist:
            pacientes = None
            messages.error(request, "No se encontraron pacientes.")
    elif request.user.groups.filter(name__in=['Jefes de Plataforma']).exists():
        try:
            pacientes = Paciente.objects.filter(perfil_completo=True)
            messages.info(request, "Accediendo a la lista de pacientes.")
        except Paciente.DoesNotExist:
            pacientes = None
            messages.error(request, "No se encontraron pacientes.")
    else:
        messages.error(request, "No tienes permiso para ingresar a esta información.")
        return redirect('home')
    return render(request, 'A10_Usu/listar_pacientes.html', locals())



#* #####           Update             #####
#* ########################################
@login_required
def ver_perfilout(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)
    medico = None
    paciente = None
    especialidades = Especialidad.objects.all()
    sistemas = SistemaSalud.objects.all()

    if user.groups.filter(name='Medicos').exists():
        medico = get_object_or_404(Medico, user=user)
        especialidades_actuales = medico.especialidad.all()
        sistemas_actuales = medico.sists_salud.all()
    elif user.groups.filter(name='Pacientes').exists():
        paciente = get_object_or_404(Paciente, user=user)
        especialidades_actuales = None
        sistemas_actuales = None
    else:
        especialidades_actuales = None
        sistemas_actuales = None

    if request.method == 'POST':
        if 'estado' in request.POST and request.user.groups.filter(name='Jefes de Plataforma').exists():
            estado = request.POST.get('estado')
            user.is_active = True if estado == 'activo' else False
            user.save()
            messages.success(request, 'El estado del usuario ha sido actualizado.')
            return redirect('A10_Usu:ver_perfilout', user_id=user.id)

        elif 'actualizar_perfil' in request.POST:
            user.tel_pers = request.POST.get('tel_pers')
            user.name_emerg = request.POST.get('name_emerg')
            user.tel_emerg = request.POST.get('tel_emerg')
            if 'imagen' in request.FILES:
                user.imagen = request.FILES['imagen']
            user.save()

            if medico:
                medico.curriculum = request.POST.get('curriculum')
                # Obtener las especialidades seleccionadas de la sesión
                especialidades_seleccionadas = request.session.get('especialidades_seleccionadas', [])
                # Obtener los sistemas de salud seleccionados de la sesión
                sistemas_seleccionados = request.session.get('sistemas_seleccionados', [])
                # Actualizar las especialidades del médico
                medico.especialidad.set(especialidades_seleccionadas)
                # Actualizar los sistemas de salud del médico
                medico.sists_salud.set(sistemas_seleccionados)
                medico.save()
                # Limpiar las variables de sesión
                request.session['especialidades_seleccionadas'] = []
                request.session['sistemas_seleccionados'] = []
            elif paciente:
                paciente.grupoSangre = request.POST.get('grupoSangre')
                paciente.enfermedades = request.POST.get('enfermedades')
                paciente.cirugias = request.POST.get('cirugias')
                paciente.alergias = request.POST.get('alergias')
                paciente.sistema_salud_id = request.POST.get('sistema_salud')
                paciente.save()

            messages.success(request, 'El perfil ha sido actualizado.')
            return redirect('A10_Usu:ver_perfilout', user_id=user.id)

        elif 'seleccionar_especialidad' in request.POST:
            especialidad_id = request.POST.get('especialidad_id')
            especialidades_seleccionadas = request.session.get('especialidades_seleccionadas', [])
            if especialidad_id not in especialidades_seleccionadas:
                especialidades_seleccionadas.append(especialidad_id)
            else:
                especialidades_seleccionadas.remove(especialidad_id)
            request.session['especialidades_seleccionadas'] = especialidades_seleccionadas
            return redirect('A10_Usu:ver_perfilout', user_id=user_id)

        elif 'seleccionar_sistema' in request.POST:
            sistema_id = request.POST.get('sistema_id')
            sistemas_seleccionados = request.session.get('sistemas_seleccionados', [])
            if sistema_id not in sistemas_seleccionados:
                sistemas_seleccionados.append(sistema_id)
            else:
                sistemas_seleccionados.remove(sistema_id)
            request.session['sistemas_seleccionados'] = sistemas_seleccionados
            return redirect('A10_Usu:ver_perfilout', user_id=user_id)

    # Inicializar las variables de sesión si no existen
    if 'especialidades_seleccionadas' not in request.session:
        request.session['especialidades_seleccionadas'] = [e.id for e in especialidades_actuales]
    if 'sistemas_seleccionados' not in request.session:
        request.session['sistemas_seleccionados'] = [s.id for s in sistemas_actuales]

    return render(request, 'A10_Usu/ver_perfilout.html', {'user': user, 'medico': medico, 'paciente': paciente, 'especialidades': especialidades, 'sistemas': sistemas, 'especialidades_actuales': especialidades_actuales, 'sistemas_actuales': sistemas_actuales, 'especialidades_seleccionadas': request.session.get('especialidades_seleccionadas', []), 'sistemas_seleccionados': request.session.get('sistemas_seleccionados', [])})

@login_required
def ver_perfilout(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)
    medico = None
    paciente = None
    especialidades = Especialidad.objects.all()
    sistemas = SistemaSalud.objects.all()

    if user.groups.filter(name='Medicos').exists():
        try:
            medico = Medico.objects.get(user=user)
            especialidades_actuales = medico.especialidad.all()
            sistemas_actuales = medico.sists_salud.all()
        except Medico.DoesNotExist:
            medico = None
            especialidades_actuales = None
            sistemas_actuales = None
    elif user.groups.filter(name='Pacientes').exists():
        try:
            paciente = Paciente.objects.get(user=user)
            especialidades_actuales = None
            sistemas_actuales = None
        except Paciente.DoesNotExist:
            paciente = None
            especialidades_actuales = None
            sistemas_actuales = None
    else:
        especialidades_actuales = None
        sistemas_actuales = None

    if request.method == 'POST':
        if 'estado' in request.POST and request.user.groups.filter(name='Jefes de Plataforma').exists():
            estado = request.POST.get('estado')
            user.is_active = True if estado == 'activo' else False
            user.save()
            messages.success(request, 'El estado del usuario ha sido actualizado.')
            return redirect('A10_Usu:ver_perfilout', user_id=user.id)

        elif 'actualizar_perfil' in request.POST:
            user.tel_pers = request.POST.get('tel_pers')
            user.name_emerg = request.POST.get('name_emerg')
            user.tel_emerg = request.POST.get('tel_emerg')
            if 'imagen' in request.FILES:
                user.imagen = request.FILES['imagen']
            user.save()

            if medico:
                medico.curriculum = request.POST.get('curriculum')
                especialidades_seleccionadas = request.POST.getlist('especialidades')
                especialidades_retiradas = request.POST.getlist('retirar_especialidades')
                sistemas_seleccionados = request.POST.getlist('sistemas')
                sistemas_retirados = request.POST.getlist('retirar_sistemas')

                # Agregar nuevas especialidades sin eliminar las existentes
                medico.especialidad.add(*especialidades_seleccionadas)
                # Retirar especialidades seleccionadas
                medico.especialidad.remove(*especialidades_retiradas)

                # Agregar nuevos sistemas de salud sin eliminar los existentes
                medico.sists_salud.add(*sistemas_seleccionados)
                # Retirar sistemas de salud seleccionados
                medico.sists_salud.remove(*sistemas_retirados)

                medico.save()
            elif paciente:
                paciente.grupoSangre = request.POST.get('grupoSangre')
                paciente.enfermedades = request.POST.get('enfermedades')
                paciente.cirugias = request.POST.get('cirugias')
                paciente.alergias = request.POST.get('alergias')
                paciente.sistema_salud_id = request.POST.get('sistema_salud')
                paciente.save()

            messages.success(request, 'El perfil ha sido actualizado.')
            return redirect('A10_Usu:ver_perfilout', user_id=user.id)

    # Inicializar las variables de sesión si no existen y si no son None
    if 'especialidades_seleccionadas' not in request.session and especialidades_actuales is not None:
        request.session['especialidades_seleccionadas'] = [e.id for e in especialidades_actuales]
    if 'sistemas_seleccionados' not in request.session and sistemas_actuales is not None:
        request.session['sistemas_seleccionados'] = [s.id for s in sistemas_actuales]

    return render(request, 'A10_Usu/ver_perfilout.html', {
        'user': user,
        'medico': medico,
        'paciente': paciente,
        'especialidades': especialidades,
        'sistemas': sistemas,
        'especialidades_actuales': especialidades_actuales,
        'sistemas_actuales': sistemas_actuales,
        'especialidades_seleccionadas': request.session.get('especialidades_seleccionadas', []),
        'sistemas_seleccionados': request.session.get('sistemas_seleccionados', []),
    })



@login_required
def cambiar_rol(request):
    user = request.user
    perfiles = []
    if hasattr(user, 'paciente_profile'):
        perfiles.append(('paciente', 'Paciente'))
    if hasattr(user, 'jefeplataforma_profile'):
        perfiles.append(('jefe_plataforma', 'Jefe de Plataforma'))
    if hasattr(user, 'recepcionista_profile'):
        perfiles.append(('recepcionista', 'Recepcionista'))
    if hasattr(user, 'medico_profile'):
        perfiles.append(('medico', 'Medico'))

    if request.method == 'POST':
        perfil_seleccionado = request.POST.get('perfil')
        request.session['perfil_activo'] = perfil_seleccionado
        return redirect('home')

    return render(request, 'A10_Usu/cambiar_rol.html', {'perfiles': perfiles})




    #                 new_username = form.cleaned_data['username']

    #                 if CustomUser.objects.filter(username=new_username).exists():
    #                     messages.error(request, "Este nombre de usuario ya está en uso.")
    #                     return render(request, 'A10_Usu/completar_perfil_paciente.html', {'form': form})

    #                 # # Crear un nuevo Paciente si no existe
    #                 # if not paciente:
    #                 #     paciente = Paciente(username_original=request.user.username)

    #                 paciente.user.username = new_username
    #                 paciente.perfil_completo = True
    #                 # paciente.user.email = request.user.email
    #                 # request.user.username = new_username

    #                 # Guarda los cambios en ambos modelos
    #                 # paciente.user.save()
    #                 paciente.save()
    #                 ic(paciente.user.username)
    #                 # request.user.save()

    #                 # Actualiza la sesión
    #                 request.session['username'] = new_username

    #                 if 'new_password1' in form.cleaned_data and form.cleaned_data['new_password1']:
    #                     request.user.set_password(form.cleaned_data['new_password1'])
    #                     request.user.save()
    #                     update_session_auth_hash(request, request.user) # Actualiza la sesión


    #                 messages.success(request, 'Perfil completado exitosamente.')
    #                 return redirect('home')

    #         except ValidationError as e:
    #             messages.error(request, e)
    #             return render(request, 'A10_Usu/completar_perfil_paciente.html', {'form': form})

    #         except Exception as e:
    #             messages.error(request, f"Error al guardar el perfil: {e}")
    #             return render(request, 'A10_Usu/completar_perfil_paciente.html', {'form': form})
    # else:
    #     form = PacienteProfileForm(instance=paciente)

    # return render(request, 'A10_Usu/completar_perfil_paciente.html', {'form': form})


    # if request.method == 'POST':
    #     form = CompletarPerfilPacienteForm(request.POST, request.FILES, instance=paciente)
    #     if form.is_valid():
    #         username = form.cleaned_data['username'].strip()
    #         nueva_clave1 = form.cleaned_data.get('nueva_clave1')
    #         nueva_clave2 = form.cleaned_data.get('nueva_clave2')

    #         try:
    #             with transaction.atomic(): #Transaccion atomica
    #                 if user.username != username:
    #                     if CustomUser.objects.filter(username=username).exists():
    #                         messages.error(request, "Ya existe un usuario con ese nombre de usuario.")
    #                         return render(request, 'A10_Usu/completar_perfil_paciente.html', {'form': form})
    #                     else:
    #                         user.username = username
    #                         print(f"Guardando username: {user.username}")
    #                         print(f"Valor del username: {username}")
    #                         user.save()
    #                         update_session_auth_hash(request, request.user) #Actualizar la sesion despues de cambiar el username
    #                         print(f"username guardado: {user.username}")

    #                 if nueva_clave1 and nueva_clave2:
    #                     if nueva_clave1 != nueva_clave2:
    #                         messages.error(request, "Las contraseñas no coinciden.")
    #                         return render(request, 'A10_Usu/completar_perfil_paciente.html', {'form': form})
    #                     try:
    #                         validate_password(nueva_clave1, user)
    #                         user.set_password(nueva_clave1)
    #                         print("Guardando contraseña")
    #                         user.save()
    #                         update_session_auth_hash(request, request.user) #Actualizar la sesion despues de cambiar la contraseña
    #                         print("Contraseña guardada")
    #                     except Exception as error:
    #                         messages.error(request, error)
    #                         return render(request, 'A10_Usu/completar_perfil_paciente.html', {'form': form})
    #                 paciente = form.save()
    #                 paciente.perfil_completo = True
    #                 paciente.save()
    #                 print(f"Paciente guardado: {paciente}")
    #                 print(f"ID del paciente guardado: {paciente.id}")
    #                 print(f"ID del user guardado: {user.id}")
    #                 print(f"Username guardado en user: {user.username}")

    #         except Exception as e:
    #             logger.error(f"Error durante el guardado: {e}")
    #             messages.error(request, "Ocurrió un error al guardar los datos. Por favor, inténtelo de nuevo.")
    #             return render(request, 'A10_Usu/completar_perfil_paciente.html', {'form': form})

    #         messages.success(request, 'Tus datos han sido actualizados exitosamente!')
    #         return redirect('home')
    #     else:
    #         # ... (manejo de errores del formulario)
    #         print("Formulario invalido")
    #         print(form.errors)
    #         for field, errors in form.errors.items():
    #             for error in errors:
    #                 messages.error(request, f"Error en {field}: {error}")
    # else:
    #     form = CompletarPerfilPacienteForm(instance=paciente)
    #     # user = paciente.customuser_ptr
    #     # print(f"Username en la inicializacion del formulario GET: {user.username}") #Imprime username en GET
    # return render(request, 'A10_Usu/completar_perfil_paciente.html', {'form': form})





#* Listado de Medicamentos más comunes
# Nombre Genérico 	    Nombre Comercial	Laboratorio	Forma Farmacéutica	Presentación	Descripción
# Paracetamol	        Tylenol	            Janssen	    Tableta	            500mg	        Analgésico y antipirético
# Ibuprofeno	        Advil	            Pfizer	    Cápsula	            200mg	        Antiinflamatorio no esteroideo
# Amoxicilina           Amoxil	            GSK	        Cápsula	            500mg	        Antibiótico
# Omeprazol	            Prilosec	        AstraZeneca	Cápsula	            20mg	        Inhibidor de la bomba de protones
# Loratadina	        Claritin	        Bayer	    Tableta	            10mg	        Antihistamínico
# Metformina	        Glucophage	        Merck	    Tableta	            500mg	        Antidiabético
# Atorvastatina	        Lipitor	            Pfizer	    Tableta	            20mg	        Estatinas
# Ácido Acetilsalicílico Aspirina	        Bayer	    Tableta	            100mg	        Antiagregante plaquetario
# Enalapril	            Vasotec	            Merck	    Tableta	            10mg	        Inhibidor de la ECA
# Levotiroxina	        Eutirox	            Merck	    Tableta	            100mcg	        Hormona tiroidea