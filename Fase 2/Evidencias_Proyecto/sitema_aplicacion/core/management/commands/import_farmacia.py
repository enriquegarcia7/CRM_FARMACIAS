import csv
from django.core.management.base import BaseCommand
from core.models import Cliente, Transaccion

class Command(BaseCommand):
    help = 'Importa datos desde un archivo CSV con columnas: nombre_cliente, correo_cliente, telefono, producto, cantidad, precio_unitario, fecha, proveedor.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Ruta al archivo CSV a importar.')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cliente, _ = Cliente.objects.get_or_create(
                    correo=row['correo_cliente'],
                    defaults={
                        'nombre': row['nombre_cliente'],
                        'telefono': row.get('telefono')
                    }
                )
                Transaccion.objects.update_or_create(
                    cliente=cliente,
                    producto=row['producto'],
                    fecha=row['fecha'],
                    defaults={
                        'cantidad': row['cantidad'],
                        'precio_unitario': row['precio_unitario'],
                        'proveedor': row['proveedor']
                    }
                )
        self.stdout.write(self.style.SUCCESS("Importación completada correctamente"))
