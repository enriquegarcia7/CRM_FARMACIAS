import pandas as pd
import logging
from decimal import Decimal
from datetime import datetime, timedelta
import re
import os
from io import BytesIO

logger = logging.getLogger(__name__)

class ExcelOfferParser:
    """
    Parser inteligente de archivos Excel/CSV que mapea automáticamente columnas
    a los campos de la base de datos, sin importar el formato del laboratorio.

    Mapeo a Base de Datos:
    - core_producto.nombre ← producto/medicamento/descripcion/item
    - core_producto.codigo ← barcode/codigo/sku/ean
    - core_producto.descripcion ← principio activo
    - ofertas_laboratorio.laboratorio ← laboratorio/proveedor
    - ofertas_laboratorio.precio_normal ← precio/pvp/valor
    - ofertas_laboratorio.precio_oferta ← oferta/precio oferta
    - ofertas_laboratorio.descuento ← %desc/descuento
    - ofertas_laboratorio.fecha_fin ← vencimiento/vigencia
    """

    # Mapeo robusto: Campo BD -> Variaciones posibles en Excel
    COLUMN_MAPPINGS = {
        # PARA core_producto.nombre (nombre del medicamento)
        'producto': [
            'descripcion', 'descripción',
            'producto', 'productos', 'product',
            'medicamento', 'medicamentos',
            'nombre', 'item', 'articulo', 'artículo'
        ],

        # PARA core_producto.codigo (código único del producto)
        'codigo': [
            'barcode', 'bar code',
            'codigo', 'código', 'cod',
            'sku', 'ean', 'upc',
            'code', 'id producto'
        ],

        # PARA ofertas_laboratorio.precio_normal (precio sin descuento)
        'precio_normal': [
            'precio', 'precios',
            'precio normal', 'precio lista',
            'pvp', 'precio venta publico',
            'valor', 'precio unitario',
            'total neto', 'neto'
        ],

        # PARA ofertas_laboratorio.precio_oferta (precio con descuento)
        'precio_oferta': [
            'oferta', 'ofertas',
            'precio oferta', 'precio promocion', 'precio promoción',
            'precio promo', 'promo',
            'precio especial', 'precio descuento'
        ],

        # PARA ofertas_laboratorio.descuento (% de descuento)
        'descuento': [
            '%desc', '% desc', '%descuento', '% descuento',
            'desc', 'descuento', 'dto',
            '%', 'porcentaje', 'pct'
        ],

        # PARA ofertas_laboratorio.laboratorio Y core_proveedor.nombre
        'laboratorio': [
            'laboratorio', 'laboratorios', 'lab',
            'proveedor', 'proveedores',
            'marca', 'fabricante'
        ],

        # PARA ofertas_laboratorio.fecha_fin (vencimiento de la oferta)
        'vigencia': [
            'vencimiento', 'vencim', 'vence',
            'vigencia', 'vigente hasta',
            'valido hasta', 'válido hasta',
            'hasta', 'fecha', 'fecha fin',
            'fecha vencimiento', 'fecha vigencia'
        ],

        # PARA core_producto.descripcion (composición del medicamento)
        'principio_activo': [
            'principio activo', 'principio', 'pa',
            'activo', 'componente', 'composicion', 'composición',
            'formula', 'fórmula', 'ingrediente activo'
        ]
    }

    def __init__(self, file_data, filename='unknown.xlsx', metadata=None):
        self.file_data = file_data
        self.filename = filename
        self.metadata = metadata or {}
        self.df = None
        self.offers = []
        self.fecha_email = None
        self.vigencia_global = None
        self.laboratorio_global = None

    def _find_header_row(self, df_temp):
        """
        Busca inteligentemente la fila que contiene los encabezados.
        Analiza las primeras 30 filas y busca aquella con más coincidencias
        con palabras clave conocidas de laboratorios.

        Returns:
            int: Índice de la fila con los encabezados (0-based)
        """
        # Crear lista de TODAS las palabras clave posibles desde COLUMN_MAPPINGS
        all_keywords = []
        for field_variations in self.COLUMN_MAPPINGS.values():
            all_keywords.extend(field_variations)

        # Normalizar keywords (minúsculas, sin tildes)
        all_keywords = [kw.lower().strip() for kw in all_keywords]

        best_row = 0
        best_score = 0

        # Buscar en las primeras 30 filas
        for idx in range(min(30, len(df_temp))):
            row = df_temp.iloc[idx]

            # Contar celdas no vacías
            non_empty_cells = sum(1 for cell in row if pd.notna(cell) and str(cell).strip())

            # Si la fila está casi vacía, skip
            if non_empty_cells < 3:
                continue

            # Convertir toda la fila a texto normalizado
            row_values = [str(cell).lower().strip() for cell in row if pd.notna(cell)]

            # Contar coincidencias exactas y parciales
            score = 0
            for cell_value in row_values:
                # Coincidencia exacta
                if cell_value in all_keywords:
                    score += 3
                # Coincidencia parcial (la keyword está contenida)
                elif any(kw in cell_value for kw in all_keywords if len(kw) > 3):
                    score += 2
                # Coincidencia inversa (el cell contiene la keyword)
                elif any(cell_value in kw for kw in all_keywords if len(cell_value) > 3):
                    score += 1

            logger.debug(f"Fila {idx}: {non_empty_cells} celdas, score={score}")

            if score > best_score:
                best_score = score
                best_row = idx

        logger.info(f"✅ Encabezados encontrados en fila {best_row} (score: {best_score})")
        return best_row

    def _extract_email_date(self):
        """Extrae la fecha del email desde metadata"""
        from datetime import datetime

        email_date_str = self.metadata.get('date', '')
        if email_date_str:
            try:
                # Formato típico de Gmail: "Thu, 31 Oct 2024 10:30:00 -0300"
                from email.utils import parsedate_to_datetime
                email_date = parsedate_to_datetime(email_date_str)
                return email_date.date()
            except:
                pass

        # Si no hay fecha del email, usar fecha actual
        return datetime.now().date()

    def _extract_vigencia_global(self, all_sheets_data):
        """
        Busca la vigencia en TODAS las hojas/páginas del documento.
        Analiza encabezados, notas, cualquier celda con información de fechas.

        Args:
            all_sheets_data: Lista de DataFrames (una por cada hoja)
        """
        from datetime import datetime, timedelta
        import re

        # Buscar en todas las hojas
        for df_temp in all_sheets_data:
            # Buscar en las primeras 20 filas de cada hoja
            for idx in range(min(20, len(df_temp))):
                row = df_temp.iloc[idx]
                row_text = ' '.join([str(cell) for cell in row if pd.notna(cell)])
                row_lower = row_text.lower()

                # Patrones de vigencia
                patterns = {
                    'hasta_dia': r'hasta\s+el\s+(lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)',
                    'vigente_hasta': r'vigente?\s+hasta:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                    'valido_hasta': r'v[áa]lido?\s+hasta:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                    'vencimiento': r'vencimiento:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                    'actualizado': r'actualizado\s+al?:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
                }

                # Buscar "hasta el día de la semana"
                dias_semana = {
                    'lunes': 0, 'martes': 1, 'miercoles': 2, 'miércoles': 2,
                    'jueves': 3, 'viernes': 4, 'sabado': 5, 'sábado': 5, 'domingo': 6
                }

                for dia_nombre, dia_num in dias_semana.items():
                    if f'hasta el {dia_nombre}' in row_lower or f'hasta {dia_nombre}' in row_lower:
                        # Buscar fecha de referencia
                        fecha_ref = self.fecha_email if self.fecha_email else datetime.now().date()

                        # Calcular próximo día de la semana
                        dias_hasta = (dia_num - fecha_ref.weekday()) % 7
                        if dias_hasta == 0:
                            dias_hasta = 7

                        vigencia = fecha_ref + timedelta(days=dias_hasta)
                        logger.info(f"📅 Vigencia: hasta el {dia_nombre} ({vigencia}) - {(vigencia - fecha_ref).days} días")
                        return vigencia

                # Buscar fechas explícitas
                for pattern_name, pattern in patterns.items():
                    match = re.search(pattern, row_lower)
                    if match:
                        fecha_str = match.group(1)
                        for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%d-%m-%y', '%d/%m/%y']:
                            try:
                                vigencia = datetime.strptime(fecha_str, fmt).date()
                                dias_vigencia = (vigencia - (self.fecha_email or datetime.now().date())).days
                                logger.info(f"📅 Vigencia extraída: {vigencia} ({dias_vigencia} días)")
                                return vigencia
                            except:
                                continue

        # Default: 30 días desde la fecha del email
        default_vigencia = (self.fecha_email or datetime.now().date()) + timedelta(days=30)
        logger.warning(f"⚠️ Vigencia no encontrada, usando default: {default_vigencia} (30 días)")
        return default_vigencia

    def _extract_laboratorio_global(self, all_sheets_data):
        """
        Extrae el nombre del laboratorio analizando:
        1. Nombre del archivo (prioridad alta)
        2. Contenido de las primeras filas de todas las hojas
        3. Columna 'laboratorio' si existe
        """
        # Primero desde nombre de archivo
        filename_clean = self.filename.lower().replace('.xlsx', '').replace('.xls', '').replace('.csv', '').replace('.xlsm', '')

        known_labs = {
            'mediven': 'Mediven', 'socofar': 'Socofar', 'labchile': 'LabChile',
            'lab chile': 'LabChile', 'cruz verde': 'Cruz Verde', 'salcobrand': 'Salcobrand',
            'cofasa': 'Cofasa', 'farmacias ahumada': 'Farmacias Ahumada'
        }

        # Buscar en nombre de archivo
        for lab_key, lab_name in known_labs.items():
            if lab_key in filename_clean:
                logger.info(f"🏭 Laboratorio desde archivo: {lab_name}")
                return lab_name

        # Buscar en contenido de las hojas
        for df_temp in all_sheets_data:
            for idx in range(min(10, len(df_temp))):
                row = df_temp.iloc[idx]
                row_text = ' '.join([str(cell) for cell in row if pd.notna(cell)]).lower()

                for lab_key, lab_name in known_labs.items():
                    if lab_key in row_text:
                        logger.info(f"🏭 Laboratorio desde contenido: {lab_name}")
                        return lab_name

        # Extraer del filename como fallback
        first_word = filename_clean.split('_')[0].split('-')[0].strip()
        if first_word and len(first_word) > 2:
            logger.info(f"🏭 Laboratorio inferido del filename: {first_word.title()}")
            return first_word.title()

        return 'Laboratorio Desconocido'

    def parse(self):
        try:
            # Extraer fecha del email (fecha de inicio)
            self.fecha_email = self._extract_email_date()
            logger.info(f"📧 Email recibido: {self.fecha_email}")

            # Detectar el tipo de archivo y usar el engine correcto
            file_ext = os.path.splitext(self.filename.lower())[1]

            # Leer TODAS las hojas del documento
            all_sheets_data = []

            if isinstance(self.file_data, bytes):
                # Convertir bytes a BytesIO para evitar warnings
                file_buffer = BytesIO(self.file_data)

                if file_ext == '.csv':
                    # CSV: solo una "hoja"
                    try:
                        df_csv = pd.read_csv(file_buffer, encoding='utf-8')
                    except:
                        file_buffer.seek(0)
                        try:
                            df_csv = pd.read_csv(file_buffer, encoding='latin-1')
                        except:
                            file_buffer.seek(0)
                            df_csv = pd.read_csv(file_buffer, encoding='iso-8859-1', sep=';')

                    all_sheets_data.append(df_csv)
                    logger.info(f"📄 CSV leído: {len(df_csv)} filas")

                elif file_ext == '.xls':
                    # XLS: leer TODAS las hojas
                    all_sheets_dict = pd.read_excel(file_buffer, engine='xlrd', sheet_name=None, header=None)

                    logger.info(f"📗 .XLS con {len(all_sheets_dict)} hoja(s): {list(all_sheets_dict.keys())}")

                    for sheet_name, df_temp in all_sheets_dict.items():
                        # Buscar encabezados en cada hoja
                        header_row = self._find_header_row(df_temp)

                        # Releer la hoja con el header correcto
                        file_buffer.seek(0)
                        df_sheet = pd.read_excel(file_buffer, engine='xlrd', sheet_name=sheet_name, header=header_row)

                        all_sheets_data.append(df_temp)  # Guardar df_temp para análisis global
                        logger.info(f"  └─ Hoja '{sheet_name}': {len(df_sheet)} filas, headers en fila {header_row}")

                elif file_ext in ['.xlsx', '.xlsm']:
                    # XLSX: leer TODAS las hojas
                    all_sheets_dict = pd.read_excel(file_buffer, engine='openpyxl', sheet_name=None, header=None)

                    logger.info(f"📘 .XLSX con {len(all_sheets_dict)} hoja(s): {list(all_sheets_dict.keys())}")

                    for sheet_name, df_temp in all_sheets_dict.items():
                        # Buscar encabezados en cada hoja
                        header_row = self._find_header_row(df_temp)

                        # Releer la hoja con el header correcto
                        file_buffer.seek(0)
                        df_sheet = pd.read_excel(file_buffer, engine='openpyxl', sheet_name=sheet_name, header=header_row)

                        all_sheets_data.append(df_temp)  # Guardar df_temp para análisis global
                        logger.info(f"  └─ Hoja '{sheet_name}': {len(df_sheet)} filas, headers en fila {header_row}")
                else:
                    # Intentar auto-detectar
                    logger.warning("⚠️ Extensión desconocida, intentando auto-detectar...")
                    all_sheets_dict = pd.read_excel(file_buffer, sheet_name=None, header=None)
                    for sheet_name, df_temp in all_sheets_dict.items():
                        all_sheets_data.append(df_temp)
            else:
                # Si no es bytes, usar método estándar
                all_sheets_dict = pd.read_excel(self.file_data, sheet_name=None, header=None)
                for sheet_name, df_temp in all_sheets_dict.items():
                    all_sheets_data.append(df_temp)

            # === EXTRAER INFORMACIÓN GLOBAL del documento ===
            self.vigencia_global = self._extract_vigencia_global(all_sheets_data)
            self.laboratorio_global = self._extract_laboratorio_global(all_sheets_data)

            logger.info(f"🏭 Laboratorio: {self.laboratorio_global}")
            logger.info(f"📅 Vigencia: {self.vigencia_global} ({(self.vigencia_global - self.fecha_email).days} días)")

            # === PROCESAR CADA HOJA y extraer ofertas ===
            total_offers = []

            # Necesitamos volver a leer las hojas con los headers correctos para procesar datos
            if file_ext == '.csv':
                # CSV ya está en all_sheets_data[0] normalizado
                self.df = all_sheets_data[0]
                self.df.columns = self.df.columns.str.lower().str.strip()
                column_map = self._detect_columns()

                if column_map.get('producto'):
                    offers = self._extract_offers_with_global_info(column_map)
                    total_offers.extend(offers)
                    logger.info(f"  ✓ CSV: {len(offers)} ofertas")

            elif file_ext in ['.xls', '.xlsx', '.xlsm']:
                # Releer todas las hojas con headers correctos
                file_buffer.seek(0)
                engine = 'xlrd' if file_ext == '.xls' else 'openpyxl'
                all_sheets_dict = pd.read_excel(file_buffer, engine=engine, sheet_name=None, header=None)

                for sheet_name, df_temp in all_sheets_dict.items():
                    header_row = self._find_header_row(df_temp)

                    # Releer con header correcto
                    file_buffer.seek(0)
                    self.df = pd.read_excel(file_buffer, engine=engine, sheet_name=sheet_name, header=header_row)

                    # Normalizar columnas
                    self.df.columns = self.df.columns.str.lower().str.strip()
                    column_map = self._detect_columns()

                    if column_map.get('producto'):
                        offers = self._extract_offers_with_global_info(column_map)
                        total_offers.extend(offers)
                        logger.info(f"  ✓ Hoja '{sheet_name}': {len(offers)} ofertas")
                    else:
                        logger.warning(f"  ⚠️ Hoja '{sheet_name}': sin columna 'producto', ignorando")

            self.offers = total_offers
            logger.info(f"✅ TOTAL: {len(self.offers)} ofertas desde {self.filename}")
            return self.offers
        except Exception as e:
            logger.error(f"Error parsing Excel: {e}")
            raise

    def _detect_columns(self):
        column_map = {}
        for key, variations in self.COLUMN_MAPPINGS.items():
            for col in self.df.columns:
                if any(var in col for var in variations):
                    column_map[key] = col
                    break
        return column_map

    def _extract_offers_with_global_info(self, column_map):
        """
        Extrae ofertas usando información global del documento.
        Usa: self.laboratorio_global, self.vigencia_global, self.fecha_email
        """
        offers = []

        for idx, row in self.df.iterrows():
            try:
                producto = str(row.get(column_map.get('producto', ''), '')).strip()
                if not producto or producto.lower() in ['nan', 'none', '']:
                    continue

                # Código de producto (BARCODE, SKU, etc.)
                codigo = str(row.get(column_map.get('codigo', ''), '')).strip()
                if codigo and codigo.lower() in ['nan', 'none', '']:
                    codigo = None

                # Principio activo (opcional)
                principio_activo = ''
                if column_map.get('principio_activo'):
                    principio_activo = str(row.get(column_map['principio_activo'], '')).strip()
                    if principio_activo.lower() in ['nan', 'none', '']:
                        principio_activo = ''

                # Precios
                precio_normal = self._parse_price(row.get(column_map.get('precio_normal', '')))
                precio_oferta = self._parse_price(row.get(column_map.get('precio_oferta', '')))

                # Si hay % de descuento pero no precio de oferta, calcularlo
                if precio_oferta == 0 and column_map.get('descuento'):
                    desc_pct = self._parse_percentage(row.get(column_map['descuento']))
                    if desc_pct > 0 and precio_normal > 0:
                        precio_oferta = precio_normal * (1 - desc_pct / 100)

                # Calcular descuento %
                if precio_normal > 0 and precio_oferta > 0:
                    descuento = ((precio_normal - precio_oferta) / precio_normal) * 100
                else:
                    descuento = 0

                # Validar que haya al menos un precio
                if precio_normal <= 0 and precio_oferta <= 0:
                    continue

                # Vigencia de la fila (si existe) o global
                vigencia_row = self._parse_date(row.get(column_map.get('vigencia', '')))
                vigencia_final = vigencia_row if vigencia_row else self.vigencia_global

                # Laboratorio de la fila (si existe) o global
                laboratorio_final = self.laboratorio_global
                if column_map.get('laboratorio'):
                    lab_row = str(row.get(column_map['laboratorio'], '')).strip()
                    if lab_row and lab_row.lower() not in ['nan', 'none', '']:
                        laboratorio_final = lab_row

                # Descripción
                descripcion = principio_activo if principio_activo else self.filename

                # PRECIOS CHILENOS: sin decimales innecesarios
                precio_normal_int = int(precio_normal) if precio_normal == int(precio_normal) else float(precio_normal)
                precio_oferta_int = int(precio_oferta) if precio_oferta == int(precio_oferta) else float(precio_oferta)

                offers.append({
                    'producto': producto,
                    'codigo': codigo,
                    'laboratorio': laboratorio_final,
                    'precio_normal': precio_normal_int if precio_normal > 0 else precio_oferta_int,
                    'precio_oferta': precio_oferta_int if precio_oferta > 0 else precio_normal_int,
                    'descuento': round(descuento, 2),
                    'fecha_inicio': self.fecha_email,  # Fecha del email
                    'fecha_fin': vigencia_final,        # Vigencia global o de la fila
                    'activa': True,
                    'source_file': self.filename,
                    'source_email': self.metadata.get('sender', 'Unknown'),
                    'principio_activo': principio_activo,
                    'descripcion': descripcion
                })
            except Exception as e:
                logger.warning(f"Error fila {idx}: {e}")
                continue

        return offers

    def _parse_price(self, value):
        """
        Parsea precios manejando tanto formato chileno como americano.
        Formato chileno: 19.232 (19 mil) o 19.232,50 (19 mil con centavos)
        Formato americano: 19,232 (19 mil) o 19,232.50 (19 mil con centavos)
        """
        if pd.isna(value):
            return 0

        # Si ya es número, retornar directamente
        if isinstance(value, (int, float)):
            return Decimal(str(value))

        price_str = str(value).strip()

        # Remover símbolos de moneda y espacios
        price_str = re.sub(r'[$\s]', '', price_str)

        if not price_str or price_str.lower() in ['nan', 'none', '-']:
            return 0

        try:
            # Detectar formato basado en uso de punto y coma
            has_dot = '.' in price_str
            has_comma = ',' in price_str

            if has_dot and has_comma:
                # Tiene ambos: determinar cuál es decimal
                last_dot = price_str.rfind('.')
                last_comma = price_str.rfind(',')

                if last_comma > last_dot:
                    # Formato chileno: 1.234.567,89
                    price_str = price_str.replace('.', '').replace(',', '.')
                else:
                    # Formato americano: 1,234,567.89
                    price_str = price_str.replace(',', '')
            elif has_dot and not has_comma:
                # Solo punto: podría ser miles o decimal
                parts = price_str.split('.')
                if len(parts) == 2 and len(parts[1]) == 2:
                    # Probablemente decimal: 19.50
                    pass  # Dejar como está
                elif len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
                    # Separador de miles: 19.232 o 1.234.567
                    price_str = price_str.replace('.', '')
                # else: dejar como está (podría ser 19.2 o 19.23)
            elif has_comma and not has_dot:
                # Solo coma: asumir decimal chileno o separador de miles americano
                parts = price_str.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Decimal chileno: 19,50
                    price_str = price_str.replace(',', '.')
                else:
                    # Separador de miles americano: 19,232
                    price_str = price_str.replace(',', '')

            result = Decimal(price_str)
            return result
        except Exception as e:
            logger.warning(f"⚠️ No se pudo parsear precio '{value}': {e}")
            return 0

    def _parse_percentage(self, value):
        if pd.isna(value):
            return 0
        pct_str = str(value).replace('%', '').strip()
        try:
            return float(pct_str)
        except:
            return 0

    def _parse_date(self, value):
        if pd.isna(value) or not value:
            return None
        if isinstance(value, datetime):
            return value.date()
        date_str = str(value).strip()
        formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d.%m.%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        return None
