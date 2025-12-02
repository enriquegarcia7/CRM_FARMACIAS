"""
Parser especializado para archivos Excel de Provefarma.

Provefarma tiene una estructura específica:
- Headers en fila 9 (índice 8)
- 4 hojas con estructura similar
- Columnas: MUNDO, NOMBRE OFERTA O CAMPAÑA, CÓDIGO PROV, DESCRIPTOR, etc.
- LABORATORIO en columna P (hojas 1-3) o S (hoja 4)
"""

import pandas as pd
import logging
from decimal import Decimal
from datetime import timedelta
from io import BytesIO

logger = logging.getLogger(__name__)


class ProvefarmaParser:
    """Parser especializado para archivos de Provefarma"""

    # No usamos un HEADER_ROW fijo - se detecta dinámicamente por hoja

    def __init__(self, file_data, filename, metadata=None):
        self.file_data = file_data
        self.filename = filename
        self.metadata = metadata or {}
        self.offers = []

    def parse(self):
        """Parsea archivo Excel de Provefarma y retorna ofertas"""
        try:
            from datetime import datetime

            # Fecha del email
            email_date_str = self.metadata.get('date', '')
            if email_date_str:
                try:
                    fecha_email = datetime.fromisoformat(email_date_str.replace('Z', '+00:00'))
                except:
                    fecha_email = datetime.now()
            else:
                fecha_email = datetime.now()

            # Vigencia: 30 días desde el email
            vigencia_global = fecha_email + timedelta(days=30)

            logger.info(f"🏥 Provefarma - Fecha: {fecha_email}, Vigencia: {vigencia_global}")

            # Detectar engine
            file_ext = self.filename.lower().split('.')[-1]
            engine = 'xlrd' if file_ext == 'xls' else 'openpyxl'

            # Buffer para múltiples lecturas
            if isinstance(self.file_data, BytesIO):
                file_buffer = self.file_data
            elif isinstance(self.file_data, bytes):
                file_buffer = BytesIO(self.file_data)
            else:
                file_buffer = self.file_data

            # Leer nombres de hojas
            file_buffer.seek(0) if hasattr(file_buffer, 'seek') else None
            all_sheets = pd.read_excel(file_buffer, engine=engine, sheet_name=None, header=None)
            sheet_names = list(all_sheets.keys())

            logger.info(f"📚 Provefarma: {len(sheet_names)} hojas encontradas")

            total_offers = []

            for sheet_name in sheet_names:
                offers = self._parse_sheet(
                    file_buffer, sheet_name, engine,
                    fecha_email, vigencia_global
                )
                total_offers.extend(offers)
                logger.info(f"  ✓ '{sheet_name}': {len(offers)} ofertas")

            self.offers = total_offers
            logger.info(f"✅ TOTAL Provefarma: {len(self.offers)} ofertas")
            return self.offers

        except Exception as e:
            logger.error(f"❌ Error en ProvefarmaParser: {e}", exc_info=True)
            raise

    def _parse_sheet(self, file_buffer, sheet_name, engine, fecha_email, vigencia_global):
        """Parsea una hoja individual de Provefarma"""
        try:
            # Resetear buffer
            file_buffer.seek(0) if hasattr(file_buffer, 'seek') else None

            # Detectar dinámicamente la fila de headers buscando "DESCRIPTOR" y "CÓDIGO"
            header_row = None
            for test_header in range(0, 15):  # Buscar en las primeras 15 filas
                try:
                    file_buffer.seek(0) if hasattr(file_buffer, 'seek') else None
                    df_test = pd.read_excel(file_buffer, engine=engine, sheet_name=sheet_name, header=test_header)
                    df_test.columns = df_test.columns.str.strip()

                    # Buscar columnas clave
                    has_descriptor = 'DESCRIPTOR' in df_test.columns
                    has_codigo = any('CÓDIGO' in str(c).upper() for c in df_test.columns)

                    if has_descriptor and has_codigo:
                        header_row = test_header
                        logger.debug(f"   ✅ Found header row at index {header_row}")
                        break
                except:
                    continue

            # Si no se encontró header, usar default
            if header_row is None:
                header_row = 7  # Default fallback
                logger.warning(f"   ⚠️ Header not found in '{sheet_name}', using default row {header_row}")

            # Leer con el header correcto
            file_buffer.seek(0) if hasattr(file_buffer, 'seek') else None
            df = pd.read_excel(
                file_buffer,
                engine=engine,
                sheet_name=sheet_name,
                header=header_row
            )

            # Normalizar nombres de columnas
            df.columns = df.columns.str.strip()

            logger.info(f"   📋 '{sheet_name}': Shape {df.shape}, Header en fila {header_row}")

            # Verificar si existen las columnas clave
            columnas_clave = ['DESCRIPTOR', 'CÓDIGO PROV', 'LABORATORIO', 'TOTAL NETO', 'PSL FORZADO']
            for col in columnas_clave:
                existe = col in df.columns
                logger.info(f"   {'✅' if existe else '❌'} Columna '{col}': {existe}")

            offers = []
            rows_skipped_no_producto = 0
            rows_skipped_category = 0
            rows_skipped_no_price = 0

            for idx, row in df.iterrows():
                try:
                    # DESCRIPTOR = nombre del producto
                    producto = str(row.get('DESCRIPTOR', '')).strip()
                    if not producto or producto.lower() in ['nan', 'none', '']:
                        rows_skipped_no_producto += 1
                        continue

                    # Skip headers de categoría intercalados
                    if self._is_category_header(producto):
                        rows_skipped_category += 1
                        if rows_skipped_category <= 3:
                            logger.debug(f"   ⏭️ Skipping category: {producto}")
                        continue

                    # CÓDIGO PROV = código del producto
                    codigo = str(row.get('CÓDIGO PROV', '')).strip()
                    if not codigo or codigo.lower() in ['nan', 'none', '']:
                        codigo = f"PROV-{idx}"

                    # LABORATORIO = fabricante
                    laboratorio = str(row.get('LABORATORIO', 'Sin Laboratorio')).strip()
                    if not laboratorio or laboratorio.lower() in ['nan', 'none', '']:
                        laboratorio = 'Sin Laboratorio'

                    # Precios
                    precio_oferta = self._parse_price(row.get('TOTAL NETO', 0))
                    if precio_oferta <= 0:
                        precio_oferta = self._parse_price(row.get('PRECIO TRAMO 2', 0))
                    if precio_oferta <= 0:
                        precio_oferta = self._parse_price(row.get('OFERTA', 0))

                    precio_normal = self._parse_price(row.get('PSL FORZADO', 0))
                    if precio_normal <= 0:
                        precio_normal = precio_oferta

                    # Validar precios
                    if precio_normal <= 0 and precio_oferta <= 0:
                        rows_skipped_no_price += 1
                        if rows_skipped_no_price <= 3:
                            logger.debug(f"   ⏭️ No price for: {producto}")
                        continue

                    # Calcular descuento
                    if precio_normal > 0 and precio_oferta > 0 and precio_oferta < precio_normal:
                        descuento = ((precio_normal - precio_oferta) / precio_normal) * 100
                    else:
                        descuento = 0

                    offers.append({
                        'producto': producto,
                        'codigo': codigo,
                        'proveedor': 'Provefarma',
                        'laboratorio': laboratorio,
                        'precio_normal': float(precio_normal),
                        'precio_oferta': float(precio_oferta),
                        'descuento': round(descuento, 2),
                        'fecha_inicio': fecha_email,
                        'fecha_fin': vigencia_global,
                        'activa': True,
                        'source_file': self.filename,
                        'source_email': self.metadata.get('sender', 'Unknown'),
                        'principio_activo': '',
                        'descripcion': producto
                    })

                except Exception as e:
                    logger.warning(f"   ⚠️ Error fila {idx}: {e}")
                    continue

            # Resumen de procesamiento
            logger.info(f"   📊 '{sheet_name}' completada: {len(offers)} ofertas extraídas")
            logger.debug(f"   Skipped: {rows_skipped_no_producto} sin producto, {rows_skipped_category} categorías, {rows_skipped_no_price} sin precio")
            return offers

        except Exception as e:
            logger.error(f"   ❌ Error procesando hoja '{sheet_name}': {e}", exc_info=True)
            return []

    def _is_category_header(self, text):
        """Detecta si un texto es un header de categoría"""
        if not text.isupper():
            return False

        meses = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
                'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']

        return any(mes in text for mes in meses)

    def _parse_price(self, value):
        """Parsea precio en formato chileno"""
        if pd.isna(value):
            return 0

        if isinstance(value, (int, float)):
            if isinstance(value, float) and value == int(value):
                return Decimal(str(int(value)))
            return Decimal(str(round(value, 2)))

        # String
        value_str = str(value).strip()

        # Remover símbolos de moneda y espacios
        value_str = value_str.replace('$', '').replace(' ', '').strip()

        if not value_str or value_str.lower() in ['nan', 'none', '-', '']:
            return 0

        try:
            # Formato chileno: punto = miles, coma = decimal
            has_dot = '.' in value_str
            has_comma = ',' in value_str

            if has_dot and has_comma:
                # Ambos: 1.234,56 -> 1234.56
                value_str = value_str.replace('.', '').replace(',', '.')
            elif has_dot and not has_comma:
                # Solo punto: eliminar (separador de miles)
                value_str = value_str.replace('.', '')
            elif has_comma and not has_dot:
                # Solo coma: reemplazar por punto (decimal)
                value_str = value_str.replace(',', '.')

            return Decimal(value_str)

        except:
            logger.warning(f"⚠️ No se pudo parsear precio: '{value}'")
            return 0
