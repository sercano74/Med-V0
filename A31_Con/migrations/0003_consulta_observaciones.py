# Generated by Django 5.1.4 on 2025-02-21 20:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('A31_Con', '0002_medicamento_estado_medicamento_laboratorio'),
    ]

    operations = [
        migrations.AddField(
            model_name='consulta',
            name='observaciones',
            field=models.TextField(blank=True, default='Sin observaciones', help_text='Observaciones o instrucciones adicionales para el paciente sobre los exámenes.', null=True),
        ),
    ]
