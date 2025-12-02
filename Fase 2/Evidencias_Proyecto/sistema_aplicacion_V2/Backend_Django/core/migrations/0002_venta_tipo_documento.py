# Generated manually on 2025-11-04
# Agrega campo tipo_documento al modelo Venta

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='venta',
            name='tipo_documento',
            field=models.CharField(blank=True, help_text='Tipo de documento (Factura, Boleta, etc)', max_length=50, null=True),
        ),
    ]
