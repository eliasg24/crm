# Generated by Django 4.2.4 on 2023-09-07 16:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0071_alter_evento_asesor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catalogorespuestasbyetapa',
            name='etapa',
            field=models.CharField(choices=[('No contactado', 'No contactado'), ('Interaccion', 'Interaccion'), ('Oportunidad', 'Oportunidad'), ('Pedido', 'Pedido'), ('Desistido', 'Desistido')], max_length=50),
        ),
    ]
