# Generated by Django 3.0.4 on 2021-11-14 23:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0005_auto_20211114_1702'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehiculo',
            name='configuracion',
            field=models.CharField(blank=True, choices=[('S2.D2', 'S2.D2'), ('S2.D2.D2', 'S2.D2.D2'), ('S2.D2.D2.T4.T4', 'S2.D2.D2.T4.T4'), ('S2.D4', 'S2.D4'), ('S2.D4.SP1', 'S2.D4.SP1'), ('S2.D4.C4.SP1', 'S2.D4.C4.SP1'), ('S2.D4.D4', 'S2.D4.D4'), ('S2.D4.D4.D4', 'S2.D4.D4.D4'), ('S2.D4.D4.L2', 'S2.D4.D4.L2'), ('S2.D4.D4.SP1', 'S2.D4.D4.SP1'), ('S2.D4.D4.T4.T4', 'S2.D4.D4.T4.T4'), ('S2.D4.L4', 'S2.D4.L4'), ('S2.L2.D4', 'S2.L2.D4'), ('S2.L2.D4.D4', 'S2.L2.D4.D4'), ('S2.L2.D4.D4.D2', 'S2.L2.D4.D4.D2'), ('S2.L2.D4.D4.L2', 'S2.L2.D4.D4.L2'), ('S2.L2.D4.D4.L4', 'S2.L2.D4.D4.L4'), ('S2.L2.L2.D4.D4', 'S2.L2.L2.D4.D4'), ('S2.L2.L2.D4.D4.L2', 'S2.L2.L2.D4.D4.L2'), ('S2.L2.L2.L2.D4.D4', 'S2.L2.L2.L2.D4.D4'), ('S2.L2.L2.L2.L2.D4.D4', 'S2.L2.L2.L2.L2.D4.D4'), ('S2.L4.D4', 'S2.L4.D4'), ('S2.L4.D4.D4', 'S2.L4.D4.D4'), ('T4.T4', 'T4.T4')], max_length=200, null=True),
        ),
    ]
