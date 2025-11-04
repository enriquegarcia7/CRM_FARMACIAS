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
            'descripcion', 'descripción', 'descrip',
            'descriptor',  # ✅ Provefarma usa "descriptor"
            'producto', 'productos', 'product',
            'medicamento', 'medicamentos', 'med',
            'nombre', 'item', 'articulo', 'artículo',
            'detalle', 'glosa', 'nombre producto',
            'producto/descripcion', 'nombre del producto'
        ],

        # PARA core_producto.codigo (código único del producto)
        'codigo': [
            'barcode', 'bar code',
            'codigo', 'código', 'cod', 'cod.',
            'codigo prov',  # ✅ Provefarma usa "CÓDIGO PROV"
            'sku', 'ean', 'upc',
            'code', 'id producto', 'id',
            'codigo producto', 'código producto',
            'nro', 'numero', 'número'
        ],

        # PARA ofertas_laboratorio.precio_normal (precio sin descuento)
        'precio_normal': [
            'precio', 'precios',
            'precio normal', 'precio lista',
            'pvp', 'precio venta publico', 'p.v.p',
            'valor', 'precio unitario', 'precio unidad',
            'total neto', 'neto',
            'precio sin descuento', 'precio anterior',
            'precio publico', 'precio público'
        ],

        # PARA ofertas_laboratorio.precio_oferta (precio con descuento)
        'precio_oferta': [
            'precio oferta', 'precio promocion', 'precio promoción',
            'precio promo', 'promo',
            'precio especial', 'precio descuento',
            'precio con descuento', 'precio final',
            'precio neto', 'precio oferta neto',
            'precio tramo',  # ✅ Provefarma usa "PRECIO TRAMO 2"
            'total neto'  # ✅ Provefarma también usa "TOTAL NETO"
        ],

        # PARA ofertas_laboratorio.descuento (% de descuento)
        'descuento': [
            '%desc', '% desc', '%descuento', '% descuento',
            'desc', 'descuento', 'dto', 'dcto',
            '%', 'porcentaje', 'pct',
            'descto', 'dsct', 'desc.'
        ],

        # PARA ofertas_laboratorio.laboratorio Y core_proveedor.nombre
        'laboratorio': [
            'laboratorio', 'laboratorios', 'lab', 'lab.',
            'proveedor', 'proveedores', 'prov',
            'marca', 'fabricante',
            'laboratorio fabricante', 'fabricante/laboratorio'
        ],

        # PARA ofertas_laboratorio.fecha_fin (vencimiento de la oferta)
        'vigencia': [
            'vencimiento', 'vencim', 'vence',
            'vigencia', 'vigente hasta',
            'valido hasta', 'válido hasta',
            'hasta', 'fecha', 'fecha fin',
            'fecha vencimiento', 'fecha vigencia',
            'fecha termino', 'fecha término'
        ],

        # PARA core_producto.descripcion (composición del medicamento)
        'principio_activo': [
            'principio activo', 'principio', 'pa', 'p.a',
            'activo', 'componente', 'composicion', 'composición',
            'formula', 'fórmula', 'ingrediente activo',
            'compuesto', 'sustancia activa'
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
        self.proveedor_global = None  # Proveedor que envía el archivo (Mediven, Socofar, etc.)

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

    def _extract_proveedor_from_email(self):
        """
        Extrae el nombre del PROVEEDOR desde el dominio del email.

        IMPORTANTE: El PROVEEDOR es quien envía el correo (Mediven, Socofar, etc.)
        NO confundir con LABORATORIO (fabricante del producto: 3M, Abbott, etc.)

        Prioridad:
        1. Buscar en archivo Excel (logo, nombre en encabezados)
        2. Extraer del dominio del email (ej: @mediven.cl → Mediven)
        3. Si el dominio es genérico (gmail.com), NO usar como proveedor

        Returns:
            str or None: Nombre del proveedor o None si es dominio genérico
        """
        sender = self.metadata.get('sender', '')

        if not sender or '@' not in sender:
            return None

        try:
            # Extraer dominio del email
            # Formato puede ser: "Nombre <email@dominio.com>" o "email@dominio.com"
            if '<' in sender and '>' in sender:
                # Formato: "Nombre Apellido <email@dominio.com>"
                email_part = sender.split('<')[1].split('>')[0].strip()
            else:
                email_part = sender.strip()

            # Obtener dominio
            domain = email_part.split('@')[1].lower()

            # Lista de dominios genéricos que NO son proveedores
            generic_domains = [
                'gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com',
                'live.com', 'icloud.com', 'aol.com', 'protonmail.com'
            ]

            # Si es dominio genérico, NO usar como proveedor
            if domain in generic_domains:
                logger.info(f"🔍 Dominio genérico detectado ({domain}), NO se usará como proveedor")
                return None

            # Extraer nombre del proveedor del dominio
            # mediven.cl → Mediven
            # socofar.com.cl → Socofar
            domain_name = domain.split('.')[0]

            # Diccionario de proveedores conocidos (para normalización)
            known_providers = {
                'mediven': 'Mediven',
                'socofar': 'Socofar',
                'labchile': 'LabChile',
                'cofasa': 'Cofasa',
                'drogueria': 'Droguería',
                'farmacias': 'Farmacias'
            }

            # Normalizar nombre si está en el diccionario
            proveedor = known_providers.get(domain_name.lower(), domain_name.title())

            logger.info(f"🏢 Proveedor extraído del email: {proveedor} (de {sender})")
            return proveedor

        except Exception as e:
            logger.warning(f"No se pudo extraer proveedor del email: {e}")
            return None

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

    def _extract_proveedor_from_file(self, all_sheets_data):
        """
        Extrae el nombre del PROVEEDOR desde el archivo Excel/CSV.

        IMPORTANTE: Busca el PROVEEDOR (Mediven, Socofar, etc.) que envía el archivo,
        NO el laboratorio fabricante de los productos (3M, Abbott, etc.).

        Busca en:
        1. Nombre del archivo (prioridad alta)
        2. Primeras filas del documento (logos, encabezados, títulos)
        3. Metadata del archivo

        Returns:
            str or None: Nombre del proveedor o None si no se encuentra
        """
        # Primero desde nombre de archivo
        filename_clean = self.filename.lower().replace('.xlsx', '').replace('.xls', '').replace('.csv', '').replace('.xlsm', '')

        # Diccionario de proveedores conocidos (empresas que envían archivos de ofertas)
        known_providers = {
            'mediven': 'Mediven',
            'socofar': 'Socofar',
            'provefarma': 'Provefarma',  # ✅ Agregado Provefarma
            'labchile': 'LabChile',
            'lab chile': 'LabChile',
            'cofasa': 'Cofasa',
            'cruz verde': 'Cruz Verde',
            'salcobrand': 'Salcobrand',
            'farmacias ahumada': 'Farmacias Ahumada',
            'drogueria': 'Droguería',
            'farmacias': 'Farmacias'
        }

        # Buscar en nombre de archivo
        for prov_key, prov_name in known_providers.items():
            if prov_key in filename_clean:
                logger.info(f"🏢 Proveedor desde filename: {prov_name}")
                return prov_name

        # Buscar en contenido de las primeras filas del archivo
        for df_temp in all_sheets_data:
            for idx in range(min(10, len(df_temp))):
                row = df_temp.iloc[idx]
                row_text = ' '.join([str(cell) for cell in row if pd.notna(cell)]).lower()

                for prov_key, prov_name in known_providers.items():
                    if prov_key in row_text:
                        logger.info(f"🏢 Proveedor desde contenido: {prov_name}")
                        return prov_name

        # Si no se encuentra, intentar extraer del filename (fallback)
        first_word = filename_clean.split('_')[0].split('-')[0].strip()
        if first_word and len(first_word) > 3:
            # Solo usar si no es un nombre genérico
            generic_names = ['lista', 'ofertas', 'precios', 'productos', 'catalogo', 'file']
            if first_word not in generic_names:
                logger.info(f"🏢 Proveedor inferido del filename: {first_word.title()}")
                return first_word.title()

        # No se pudo determinar el proveedor desde el archivo
        logger.warning("⚠️ No se pudo extraer proveedor del archivo")
        return None

    def parse(self):
        try:
            # Extraer fecha del email (fecha de inicio)
            self.fecha_email = self._extract_email_date()
            logger.info(f"📧 Email recibido: {self.fecha_email}")

            # ✅ DETECCIÓN DE PROVEFARMA: Usar parser especializado
            if 'provefarma' in self.filename.lower():
                logger.info(f"🏥 Archivo Provefarma detectado, usando parser especializado")
                from core.parsers.provefarma_parser import ProvefarmaParser
                parser = ProvefarmaParser(self.file_data, self.filename, self.metadata)
                self.offers = parser.parse()
                return self.offers

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

            # Extraer PROVEEDOR con VALIDACIÓN DE CONSISTENCIA
            # El proveedor debe ser UNO SOLO y consistente entre archivo y email
            proveedor_archivo = self._extract_proveedor_from_file(all_sheets_data)
            proveedor_email = self._extract_proveedor_from_email()

            # VALIDACIÓN: El proveedor del archivo y del email deben coincidir
            if proveedor_archivo and proveedor_email:
                # Ambos encontrados: validar que sean el mismo
                if proveedor_archivo.lower() != proveedor_email.lower():
                    logger.error(f"❌ INCONSISTENCIA DETECTADA:")
                    logger.error(f"   Archivo: {proveedor_archivo}")
                    logger.error(f"   Email:   {proveedor_email}")
                    logger.error(f"   ⚠️  El proveedor del archivo NO coincide con el dominio del email")

                    # Usar el del archivo (es más confiable)
                    self.proveedor_global = proveedor_archivo
                    logger.warning(f"   → Usando proveedor del ARCHIVO: {self.proveedor_global}")
                else:
                    # Coinciden: OK
                    self.proveedor_global = proveedor_archivo
                    logger.info(f"✅ Proveedor VALIDADO: {self.proveedor_global} (archivo + email coinciden)")

            elif proveedor_archivo:
                # Solo encontrado en archivo (email es genérico como gmail.com)
                self.proveedor_global = proveedor_archivo
                logger.info(f"🏢 Proveedor FINAL: {self.proveedor_global} (desde archivo)")
                if self.metadata.get('sender', '').lower().endswith('gmail.com'):
                    logger.info(f"   ℹ️  Email desde Gmail (dominio genérico, usando proveedor del archivo)")

            elif proveedor_email:
                # Solo encontrado en email (no está en archivo)
                self.proveedor_global = proveedor_email
                logger.warning(f"⚠️ Proveedor FINAL: {self.proveedor_global} (solo desde email, no encontrado en archivo)")

            else:
                # No se pudo determinar el proveedor
                self.proveedor_global = 'Proveedor Desconocido'
                logger.error(f"❌ Proveedor FINAL: {self.proveedor_global} (no se pudo determinar)")

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
        """Detecta columnas del Excel y las mapea a campos de la BD"""
        column_map = {}

        # Log de columnas disponibles
        logger.info(f"📋 Columnas disponibles en Excel: {list(self.df.columns)}")

        for key, variations in self.COLUMN_MAPPINGS.items():
            for col in self.df.columns:
                if any(var in col for var in variations):
                    column_map[key] = col
                    logger.info(f"  ✓ Detectado '{key}' -> '{col}'")
                    break

        # Log de columnas NO detectadas
        missing = [k for k in ['producto', 'codigo', 'laboratorio'] if k not in column_map]
        if missing:
            logger.warning(f"⚠️ Columnas NO detectadas: {missing}")

        # Log del mapeo final
        logger.info(f"🗺️ Mapeo de columnas: {column_map}")

        return column_map

    def _extract_offers_with_global_info(self, column_map):
        """
        Extrae ofertas usando información global del documento.

        Usa:
        - self.proveedor_global: Quien envía el archivo (Mediven, Socofar, etc.)
        - self.vigencia_global: Fecha de vencimiento de las ofertas
        - self.fecha_email: Fecha de inicio de las ofertas

        IMPORTANTE:
        - PROVEEDOR: Empresa que envía las ofertas (Mediven, Socofar, etc.)
        - LABORATORIO: Fabricante del producto (3M, Abbott Nutricion, etc.)
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

                # ⚠️ VALIDACIÓN: Skip filas que parecen ser headers de categoría
                # Ejemplo: "BIENESTAR OCTUBRE 2025" sin código ni precios
                # Solo skip si cumple TODO lo siguiente:
                # 1. No tiene código
                # 2. No tiene precio normal NI precio oferta
                # 3. El nombre es todo mayúsculas con un patrón de categoría
                if not codigo:
                    # Verificar si tiene precios válidos
                    precio_test_normal = self._parse_price(row.get(column_map.get('precio_normal', '')))
                    precio_test_oferta = self._parse_price(row.get(column_map.get('precio_oferta', '')))

                    # Si no hay precios Y el nombre parece un header de categoría
                    if precio_test_normal <= 0 and precio_test_oferta <= 0:
                        # Patrón de header: Todo mayúsculas + mes/año
                        if producto.isupper() and any(mes in producto for mes in ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']):
                            logger.info(f"⏭️ Skipping category header: '{producto}'")
                            continue

                    # Si no hay código pero SÍ hay precios, generar código automático
                    if not codigo and (precio_test_normal > 0 or precio_test_oferta > 0):
                        codigo = f"AUTO-{idx}-{producto[:10].replace(' ', '-').upper()}"
                        logger.info(f"⚠️ Producto sin código, generando automático: {codigo}")

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

                # LABORATORIO: Fabricante del producto (3M, Abbott, etc.)
                # Leer de la columna 'laboratorio' del Excel
                laboratorio_fabricante = None
                if column_map.get('laboratorio'):
                    lab_row = str(row.get(column_map['laboratorio'], '')).strip()
                    if lab_row and lab_row.lower() not in ['nan', 'none', '']:
                        laboratorio_fabricante = lab_row

                # Si no hay laboratorio en la fila, usar un valor por defecto
                if not laboratorio_fabricante:
                    laboratorio_fabricante = 'Sin Laboratorio'

                # PROVEEDOR: Empresa que envía el archivo (Mediven, Socofar, etc.)
                # Viene del análisis global del archivo + email
                proveedor_final = self.proveedor_global if self.proveedor_global else 'Proveedor Desconocido'

                # Descripción
                descripcion = principio_activo if principio_activo else self.filename

                # Usar precios como Decimal directamente (sin conversiones innecesarias)
                # Los precios ya vienen parseados correctamente desde _parse_price()
                offers.append({
                    'producto': producto,
                    'codigo': codigo,
                    'proveedor': proveedor_final,  # Quien envía el archivo (Mediven, Socofar, etc.)
                    'laboratorio': laboratorio_fabricante,  # Fabricante del producto (3M, Abbott, etc.)
                    'precio_normal': float(precio_normal) if precio_normal > 0 else float(precio_oferta),
                    'precio_oferta': float(precio_oferta) if precio_oferta > 0 else float(precio_normal),
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
        Parsea precios manejando formato chileno EXCLUSIVAMENTE.

        Formato chileno estándar:
        - 19.334 = 19334 (diecinueve mil trescientos treinta y cuatro)
        - 19.334,50 = 19334.50 (con decimales)
        - 19334 = 19334 (sin formato)

        IMPORTANTE: El punto (.) siempre es separador de miles, NO decimal.
        La coma (,) es el separador decimal en formato chileno.
        """
        if pd.isna(value):
            return 0

        # Si ya es número (pandas leyó la celda como numérico)
        if isinstance(value, (int, float)):
            # Pandas puede leer 19.334 del Excel como float 19.334
            # Pero en formato chileno esto significa 19 mil, no 19 con decimales
            # Convertir directamente a entero para números sin decimales reales
            if isinstance(value, float):
                # Verificar si tiene decimales significativos (no .0)
                if value == int(value):
                    # No tiene decimales reales, es un entero
                    return Decimal(str(int(value)))
                else:
                    # Tiene decimales reales, usar tal cual
                    # Redondear a 2 decimales para evitar errores de flotante
                    return Decimal(str(round(value, 2)))
            return Decimal(str(value))

        price_str = str(value).strip()

        # Remover símbolos de moneda y espacios
        price_str = re.sub(r'[$\s]', '', price_str)

        if not price_str or price_str.lower() in ['nan', 'none', '-', '']:
            return 0

        try:
            # Detectar formato basado en uso de punto y coma
            has_dot = '.' in price_str
            has_comma = ',' in price_str

            if has_dot and has_comma:
                # Formato chileno completo: 1.234.567,89
                # Punto = miles, Coma = decimal
                price_str = price_str.replace('.', '').replace(',', '.')

            elif has_dot and not has_comma:
                # Solo punto: en formato chileno, el punto SIEMPRE es separador de miles
                parts = price_str.split('.')

                # Casos especiales:
                # - Un solo punto con 2 dígitos después podría ser decimal americano (19.50)
                #   PERO en Chile esto sería 19 pesos con 50 centavos, escrito como 19,50
                # - Un solo punto con 3 dígitos después ES separador de miles (19.334 = 19 mil)

                if len(parts) == 2:
                    if len(parts[1]) == 3:
                        # Definitivamente separador de miles chileno: 19.334 = 19334
                        price_str = price_str.replace('.', '')
                    elif len(parts[1]) == 2:
                        # Podría ser decimal o miles
                        # En formato chileno, 19.50 NO existe, sería 19,50 o 1950
                        # Asumir que es separador de miles si el número es >1000
                        if int(parts[0]) >= 10:
                            # 19.50 se interpreta como 1950 (diecinueve pesos cincuenta centavos)
                            price_str = price_str.replace('.', '')
                        else:
                            # Números pequeños (0.50, 5.50) podrían ser decimales
                            # Dejar como decimal
                            pass
                    elif len(parts[1]) == 1:
                        # 19.5 - probablemente decimal, dejar como está
                        pass
                    else:
                        # Múltiples puntos o formato extraño: eliminar todos los puntos
                        price_str = price_str.replace('.', '')
                else:
                    # Múltiples puntos: 1.234.567 - separador de miles
                    price_str = price_str.replace('.', '')

            elif has_comma and not has_dot:
                # Solo coma: en formato chileno, coma es decimal
                # Casos:
                # - 19,50 = 19.50 (decimal)
                # - 19,5 = 19.5 (decimal)
                # - 19,334 = 19.334 (decimal, aunque extraño)
                parts = price_str.split(',')
                if len(parts) == 2:
                    # Reemplazar coma por punto para Decimal
                    price_str = price_str.replace(',', '.')
                else:
                    # Múltiples comas: formato inválido, eliminar comas
                    price_str = price_str.replace(',', '')

            result = Decimal(price_str)
            logger.debug(f"💰 Precio parseado: '{value}' → {result}")
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
