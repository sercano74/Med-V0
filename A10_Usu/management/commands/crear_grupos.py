from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from ...models import *
from A20_Hrs.models import *
from A30_Fic.models import *

#* En el CMD se debe llamar la instrucción:    python manage.py crear_grupos

class Command(BaseCommand):
    help = 'Crea los grupos y asigna los permisos iniciales.'

    def handle(self, *args, **options):
        grupos = {
            'Jefe Plataforma': {
                'codenames': [
                    'Home_JefePlataforma',
                    'add_genero', 'change_genero', 'view_genero',
                    'add_especialidad', 'change_especialidad', 'view_especialidad',
                    'add_sistema_salud', 'change_sistema_salud', 'view_sistema_salud',
                    'add_jefeplataforma', 'change_jefeplataforma', 'view_jefeplataforma'
                    'add_recepcionista', 'change_recepcionista', 'view_recepcionista',
                    'add_medico', 'change_medico', 'view_medico',
                    'add_horamedica', 'change_horamedica', 'view_horamedica',
                    # ... otros permisos
                ],
                'models': [Genero, Especialidad, SistemaSalud, JefePlataforma, Recepcionista, Medico, HoraMedica] #Modelos a los que aplica
            },
            'Recepcionista': {
                'codenames': [
                    'Home_Recepcionista',
                    'add_horamedica', 'change_horamedica', 'view_horamedica',
                    # ... otros permisos
                ],
                 'models': [HoraMedica]
            },
            'Medico': {
                'codenames': [
                    'Home_Medico',
                    'add_horamedica','add_fichamedica','change_fichamedica',
                    # ... otros permisos
                ],
                'models': [HoraMedica, FichaMedica]
            },
            'Paciente': {
                'codenames': [
                    'Home_Paciente',
                    'tomar_horamedica',
                    'view_fichamedica'
                    # ... otros permisos
                ],
                'models': [HoraMedica, FichaMedica]
            },
        }

        for nombre_grupo, data in grupos.items():
            grupo, creado = Group.objects.get_or_create(name=nombre_grupo)

            if creado:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{nombre_grupo}" creado.'))

            codenames = data['codenames']
            models = data['models']
            permisos = Permission.objects.none() #Inicializar un queryset vacio

            for model in models:
                content_type = ContentType.objects.get_for_model(model)
                permisos |= Permission.objects.filter(codename__in=codenames, content_type=content_type) #Usar OR para concatenar los querysets

            grupo.permissions.set(permisos)

            self.stdout.write(self.style.SUCCESS(f'Permisos asignados al grupo "{nombre_grupo}".'))

        self.stdout.write(self.style.SUCCESS('Grupos y permisos iniciales creados exitosamente.'))


# C:\Users\sergi\OneDrive\Escritorio\ProyectosDjango\Med\A10_Usu\management\comands\__init__.py