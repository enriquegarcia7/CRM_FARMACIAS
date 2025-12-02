"""
Comando de diagnóstico para analizar estructura de archivos Excel de Provefarma.

Uso:
    python manage.py diagnostico_excel /ruta/al/archivo.xlsx
"""

from django.core.management.base import BaseCommand
import pandas as pd
import sys


class Command(BaseCommand):
    help = 'Analiza la estructura de un archivo Excel para diagnóstico'

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str, help='Ruta al archivo Excel')

    def handle(self, *args, **options):
        archivo = options['archivo']

        try:
            # Leer todas las hojas
            all_sheets = pd.read_excel(archivo, sheet_name=None, header=None)

            self.stdout.write(self.style.SUCCESS(f'\n📄 Archivo: {archivo}\n'))
            self.stdout.write(f'📊 Total de hojas: {len(all_sheets)}\n')

            for sheet_name, df in all_sheets.items():
                self.stdout.write(self.style.WARNING(f'\n🔍 Hoja: "{sheet_name}"'))
                self.stdout.write(f'   Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas\n')

                # Mostrar primeras 3 filas
                self.stdout.write('   Primeras 3 filas:')
                for idx in range(min(3, len(df))):
                    row_data = df.iloc[idx].tolist()[:10]  # Primeras 10 columnas
                    self.stdout.write(f'   Fila {idx}: {row_data}')

                # Buscar la fila de headers
                self.stdout.write('\n   🔎 Buscando header...')
                for idx in range(min(20, len(df))):
                    row = df.iloc[idx]
                    # Contar cuántas celdas no vacías tiene
                    non_empty = row.notna().sum()
                    if non_empty >= 3:  # Al menos 3 columnas con datos
                        row_text = ' | '.join([str(cell)[:30] for cell in row[:10] if pd.notna(cell)])
                        self.stdout.write(f'   Fila {idx} ({non_empty} cols): {row_text}')

                        # Buscar palabras clave de headers
                        row_lower = str(row.tolist()).lower()
                        if any(keyword in row_lower for keyword in ['codigo', 'descriptor', 'precio', 'producto']):
                            self.stdout.write(self.style.SUCCESS(f'   ✅ POSIBLE HEADER EN FILA {idx}'))

                self.stdout.write('\n' + '-' * 80)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
            import traceback
            traceback.print_exc()
