# utils.py (un archivo separado para funciones utilitarias comunes)
from django.core.mail import send_mail
from allauth.account.utils import send_email_confirmation
# import random
import secrets
import string
from icecream import ic


def generar_clave_provisoria(length=4):
    letras              = string.ascii_letters + string.digits + string.punctuation
    # clave_provisoria    = ''.join(random.choice(letras) for i in range(length))
    clave_provisoria    = ''.join(secrets.choice(letras) for i in range(length))
    return clave_provisoria
# Usar secrets en lugar de random es crucial para la seguridad, ya que secrets está diseñado para generar números aleatorios criptográficamente seguros.


def enviar_email_clave_provisoria(usuario):
    send_mail(
        'HumanaSalud te envía una clave provisoria',
        f'{usuario.username}, su clave provisoria es {usuario.password}.\n Use esta clave para iniciar sesión, cambiar tu contraseña y completar su perfil.',
        'ordered.dev.01@gmail.com',  # Cambia esto por tu dirección de correo de envío
        [usuario.email],
        fail_silently=False,
    )
    # send_email_confirmation(usuario)
    # ic("Correo de confirmación enviado a:", email) # Debug


# def perfil_completo(user):
#     # Verifica si el perfil está completo
#     campos_requeridos = ['first_name', 'last_name', 'dni', 'f_nacim', 'genero', 't_personal', 'name_emergencia', 't_emergencia']
#     for campo in campos_requeridos:
#         if not getattr(user, campo):
#             return False
#     return True