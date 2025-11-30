import pandas as pd
import logging
import hashlib
from decimal import Decimal
from django.db import transaction, IntegrityError
from django.utils import timezone
from datetime import datetime
from core.models import Venta, DetalleVenta, Cliente, Producto, MetodoPago, EstadoVenta
import re

logger = logging.getLogger(__name__)


class SalesExcelParser:
    """
    Parser para archivos Excel de ventas históricas.

    Columnas requeridas del Excel:
    - RUT: RUT del cliente (identificador ÚNICO del cliente) ⭐ IMPORTANTE
           Formatos aceptados: "12.345.678-9", "12345678-9", "123456789"
           El parser normalizará automáticamente el formato
    - FECHA: Fecha de la venta
    - CODIGO: Código del producto
    - PRODUCTO: Nombre/descripción del producto
    - CANTIDAD: Cantidad vendida
    - PRECIO: Precio unitario

    Columnas opcionales:
    - TIPO DOCUMENTO: Tipo de documento (Factura, Boleta, etc)
    - NUMERO DOCUMENTO: Número de documento de venta
    - NOMBRE CLIENTE: Nombre del cliente
    - CORREO: Correo electrónico del cliente
    - CLIENTE_ID: ID de transacción (NO es identificador del cliente)
    - FECHA VENCIMIENTO
    - ORDEN COMPRA
    - VENDEDOR
    - DISTRIBUIDOR
    - SUCURSAL
    - CENTRO COSTO
    - DESCUENTO
    - NETO
    - CUENTA
    - FAMILIA

    IMPORTANTE:
    - RUT es el identificador ÚNICO del cliente
    - CLIENTE_ID (si existe) es solo un ID de transacción/fila, NO del cliente
    - Si el Excel tiene ambas columnas, se usa RUT para agrupar clientes

    Este formato está diseñado para análisis predictivo de demanda estacional.
    """

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.stats = {
            'ventas_insertadas': 0,
            'ventas_duplicadas': 0,
            'detalles_insertados': 0,
            'clientes_creados': 0,
            'clientes_actualizados': 0,
            'productos_creados': 0,
            'productos_no_encontrados': 0,
            'errores': []
        }

    def parse_and_load(self):
        """
        Parsea el archivo Excel y carga las ventas en la base de datos.
        """
        try:
            # Leer Excel
            df = pd.read_excel(self.file_obj, sheet_name=0)

            logger.info(f"📊 Excel de ventas cargado: {len(df)} filas")
            logger.info(f"📋 Columnas encontradas: {list(df.columns)}")

            # Normalizar nombres de columnas
            df.columns = df.columns.str.strip().str.upper()

            # Mapear columnas flexiblemente
            column_mapping = self._map_columns(df.columns)
            logger.info(f"📋 Mapeo de columnas: {column_mapping}")

            # Renombrar columnas según el mapeo
            df = df.rename(columns=column_mapping)
            logger.info(f"📋 Columnas después del mapeo: {list(df.columns)}")

            # Validar columnas requeridas después del mapeo
            # Flexibilidad: CLIENTE_ID puede ser RUT o cualquier identificador
            required_cols = ['FECHA', 'PRODUCTO', 'CANTIDAD', 'PRECIO_UNITARIO']
            missing_cols = [col for col in required_cols if col not in df.columns]

            # Validar que haya al menos un identificador de cliente
            if 'CLIENTE_ID' not in df.columns and 'RUT' not in df.columns:
                missing_cols.append('CLIENTE_ID o RUT')

            if missing_cols:
                raise ValueError(
                    f"❌ No se pudieron mapear las columnas requeridas: {missing_cols}\n"
                    f"📋 Columnas disponibles: {list(df.columns)}\n"
                    f"💡 Columnas requeridas: TIPO DOCUMENTO, NUMERO DOCUMENTO, FECHA, NOMBRE CLIENTE, CORREO, CODIGO, PRODUCTO, CANTIDAD, PRECIO, CLIENTE_ID"
                )

            # Cargar ventas
            self._load_sales(df)

            logger.info(f"✅ Ventas insertadas: {self.stats['ventas_insertadas']}")
            logger.info(f"⚠️ Ventas duplicadas (omitidas): {self.stats['ventas_duplicadas']}")
            logger.info(f"✅ Detalles insertados: {self.stats['detalles_insertados']}")
            logger.info(f"✅ Clientes creados: {self.stats['clientes_creados']}")
            logger.info(f"✅ Productos históricos creados: {self.stats['productos_creados']}")

            if self.stats['errores']:
                logger.warning(f"⚠️ Errores: {len(self.stats['errores'])}")
                for error in self.stats['errores'][:10]:  # Mostrar solo primeros 10
                    logger.warning(f"  - {error}")

            return self.stats

        except Exception as e:
            logger.error(f"❌ Error parseando Excel de ventas: {e}")
            self.stats['errores'].append(f"Error general: {str(e)}")
            raise

    def _map_columns(self, columns):
        """
        Mapea columnas del Excel a nombres estándar.
        Busca flexiblemente las columnas necesarias.
        """
        mapping = {}
        columns_upper = [col.upper() for col in columns]
        used_columns = set()  # Para evitar duplicados

        # Mapeo flexible de columnas (en orden de prioridad)
        # IMPORTANTE: RUT es el identificador ÚNICO del cliente
        # CLIENTE_ID puede ser un ID de transacción o fila, NO del cliente
        mappings = {
            'RUT': ['RUT', 'CLIENTE RUT', 'CLIENTE_RUT', 'RUT CLIENTE', 'RUT_CLIENTE'],
            'CLIENTE_ID': ['CLIENTE_ID', 'CLIENTE ID', 'ID CLIENTE', 'ID_CLIENTE'],
            'NOMBRE_CLIENTE': ['NOMBRE CLIENTE', 'NOMBRE_CLIENTE', 'NOMBRE', 'CLIENTE'],
            'CORREO': ['CORREO', 'EMAIL', 'E-MAIL', 'CORREO ELECTRONICO', 'CORREO ELECTRÓNICO', 'CORREO CLIENTE'],
            'NUMERO': ['NUMERO DOCUMENTO', 'NÚMERO DOCUMENTO', 'NUMERO_DOCUMENTO', 'NÚMERO', 'NUMERO', 'NRO', 'N°', 'NUMERO DOC'],
            'TIPO_DOCUMENTO': ['TIPO DOCUMENTO', 'TIPO_DOCUMENTO', 'TIPO'],
            'FECHA': ['FECHA'],
            'FECHA_VENCIMIENTO': ['FECHA VENCIMIENTO', 'FECHA_VENCIMIENTO', 'VENCIMIENTO'],
            'ORDEN_COMPRA': ['ORDEN COMPRA', 'ORDEN_COMPRA', 'OC'],
            'VENDEDOR': ['VENDEDOR'],
            'DISTRIBUIDOR': ['DISTRIBUIDOR'],
            'SUCURSAL': ['SUCURSAL'],
            'CENTRO_COSTO': ['CENTRO COSTO', 'CENTRO_COSTO'],
            'CODIGO': ['CODIGO', 'CÓDIGO', 'COD', 'SKU', 'CODIGO_PRODUCTO', 'CODIGO PRODUCTO'],
            'PRODUCTO': ['PRODUCTO', 'DESCRIPCION', 'DESCRIPCIÓN', 'NOMBRE_PRODUCTO', 'NOMBRE PRODUCTO'],
            'CANTIDAD': ['CANTIDAD', 'CANT', 'QTY'],
            'PRECIO_UNITARIO': ['PRECIO', 'PRECIO UNITARIO', 'PRECIO_UNITARIO', 'PRECITO UNITARIO', 'PRECIO_UNITARIO'],
            'DESCUENTO': ['DESCUENTO', 'DESCUENMENTO'],
            'NETO': ['NETO'],
            'CUENTA': ['CUENTA'],
            'FAMILIA': ['FAMILIA', 'CATEGORIA', 'CATEGORÍA'],
        }

        # Buscar cada columna estándar
        for standard_name, possible_names in mappings.items():
            for possible in possible_names:
                if possible in columns_upper and possible not in used_columns:
                    idx = columns_upper.index(possible)
                    original_col = columns[idx]
                    mapping[original_col] = standard_name
                    used_columns.add(possible)
                    break

        return mapping

    def _generar_hash_venta(self, numero, cliente_rut, fecha):
        """
        Genera un hash MD5 único para detectar ventas duplicadas.
        Hash = MD5(numero + cliente_rut + fecha_str)
        """
        # Normalizar valores
        numero_str = str(numero).strip() if numero else ''
        rut_str = str(cliente_rut).strip()
        fecha_str = fecha.strftime('%Y-%m-%d') if isinstance(fecha, datetime) else str(fecha)

        # Crear string único
        unique_string = f"{numero_str}|{rut_str}|{fecha_str}"

        # Generar hash MD5
        hash_obj = hashlib.md5(unique_string.encode('utf-8'))
        return hash_obj.hexdigest()

    @transaction.atomic
    def _load_sales(self, df):
        """
        Carga ventas en la base de datos.

        ESTRATEGIA CORREGIDA:
        - Cada FILA del Excel es un DetalleVenta independiente
        - Una Venta se agrupa por: NUMERO DOCUMENTO + FECHA + CLIENTE (RUT)
        - Primero elimina ventas existentes para evitar duplicados
        - Los códigos de producto se mantienen EXACTAMENTE como en el Excel
        """
        logger.info(f"🚀 Iniciando procesamiento de {len(df)} filas")

        # PASO 0: LIMPIAR VENTAS Y DETALLES EXISTENTES
        logger.info("🗑️ Limpiando ventas anteriores...")
        detalles_count = DetalleVenta.objects.count()
        ventas_count = Venta.objects.count()
        DetalleVenta.objects.all().delete()
        Venta.objects.all().delete()
        logger.info(f"✅ Eliminados {ventas_count} ventas y {detalles_count} detalles anteriores")

        # 1. PRE-CARGAR PRODUCTOS EN MEMORIA
        logger.info("📦 Cargando productos en memoria...")
        productos_dict = {p.codigo: p for p in Producto.objects.all()}
        logger.info(f"✅ {len(productos_dict)} productos cargados")

        # 2. PRE-CARGAR CLIENTES EN MEMORIA
        logger.info("👥 Cargando clientes en memoria...")
        clientes_dict = {c.rut: c for c in Cliente.objects.all()}
        logger.info(f"✅ {len(clientes_dict)} clientes cargados")

        # 2.5. OBTENER DEFAULTS
        metodo_pago_default = MetodoPago.objects.filter(codigo='efectivo').first()
        estado_default = EstadoVenta.objects.filter(codigo='completada').first()

        # 3. PROCESAR FILAS - Agrupar por (numero_doc, fecha, rut)
        ventas_dict = {}  # key: (numero_doc, fecha, rut) -> {venta_info, items: []}
        clientes_a_crear = {}
        productos_a_crear = {}

        logger.info("📝 Procesando filas del Excel...")
        filas_procesadas = 0
        filas_error = 0

        for index, row in df.iterrows():
            try:
                # Extraer fecha
                fecha = self._parse_fecha(row.get('FECHA'))
                if not fecha:
                    filas_error += 1
                    continue

                # Extraer RUT del cliente
                cliente_rut = self._normalize_rut(row.get('RUT', ''))
                if not cliente_rut:
                    cliente_rut = self._normalize_rut(row.get('CLIENTE_ID', ''))
                if not cliente_rut:
                    filas_error += 1
                    continue

                # Datos del cliente
                nombre_cliente = self._clean_string(row.get('NOMBRE_CLIENTE', ''))
                correo_cliente = self._clean_string(row.get('CORREO', ''))

                # Detectar si el nombre es genérico (Cliente_XXXX, Cliente General, etc.)
                nombre_es_real = self._es_nombre_real(nombre_cliente)

                if cliente_rut not in clientes_dict and cliente_rut not in clientes_a_crear:
                    # Cliente nuevo - crear
                    clientes_a_crear[cliente_rut] = {
                        'rut': cliente_rut,
                        'nombre': nombre_cliente if nombre_es_real else f'Cliente {cliente_rut}',
                        'correo': correo_cliente if correo_cliente else None,
                        'es_nuevo': True
                    }
                elif cliente_rut in clientes_a_crear and nombre_es_real:
                    # Si ya está en clientes_a_crear pero con nombre genérico, actualizar
                    if not self._es_nombre_real(clientes_a_crear[cliente_rut]['nombre']):
                        clientes_a_crear[cliente_rut]['nombre'] = nombre_cliente
                elif cliente_rut in clientes_dict and nombre_es_real:
                    # Cliente existe en BD - verificar si necesita actualización
                    cliente_existente = clientes_dict[cliente_rut]
                    if not self._es_nombre_real(cliente_existente.nombre):
                        # Agregar a clientes_a_crear para actualización
                        if cliente_rut not in clientes_a_crear:
                            clientes_a_crear[cliente_rut] = {
                                'rut': cliente_rut,
                                'nombre': nombre_cliente,
                                'correo': correo_cliente if correo_cliente else None,
                                'es_nuevo': False
                            }

                # Código y nombre del producto (EXACTAMENTE como en Excel)
                codigo_producto = self._clean_string(row.get('CODIGO', ''))
                nombre_producto = self._clean_string(row.get('PRODUCTO', ''))
                if not codigo_producto:
                    filas_error += 1
                    continue

                # Verificar si producto existe, sino crear
                if codigo_producto not in productos_dict and codigo_producto not in productos_a_crear:
                    productos_a_crear[codigo_producto] = {
                        'codigo': codigo_producto,
                        'nombre': nombre_producto if nombre_producto else f'Producto {codigo_producto}',
                        'precio_venta': self._parse_precio(row.get('PRECIO_UNITARIO', 0))
                    }

                # Cantidad y precio
                cantidad = self._parse_int(row.get('CANTIDAD', 0))
                if cantidad <= 0:
                    cantidad = 1

                precio_unitario = self._parse_precio(row.get('PRECIO_UNITARIO', 0))
                if precio_unitario <= 0:
                    neto = self._parse_precio(row.get('NETO', 0))
                    if neto > 0 and cantidad > 0:
                        precio_unitario = neto / cantidad

                # Número de documento
                numero_doc = str(row.get('NUMERO', '')).strip()

                # KEY: Agrupar por (numero_doc, fecha, cliente_rut)
                key = (numero_doc, fecha.date() if hasattr(fecha, 'date') else fecha, cliente_rut)

                if key not in ventas_dict:
                    ventas_dict[key] = {
                        'tipo_documento': self._clean_string(row.get('TIPO_DOCUMENTO', '')),
                        'numero': numero_doc,
                        'fecha': fecha,
                        'cliente_rut': cliente_rut,
                        'items': []
                    }

                # Agregar item (detalle)
                ventas_dict[key]['items'].append({
                    'codigo_producto': codigo_producto,
                    'nombre_producto': nombre_producto,
                    'cantidad': cantidad,
                    'precio_unitario': precio_unitario,
                    'neto': self._parse_precio(row.get('NETO', 0))
                })

                filas_procesadas += 1

            except Exception as e:
                filas_error += 1
                continue

        logger.info(f"✅ {filas_procesadas} filas procesadas, {filas_error} errores")
        logger.info(f"📊 {len(ventas_dict)} ventas únicas identificadas")

        # 4. CREAR CLIENTES FALTANTES Y ACTUALIZAR NOMBRES REALES
        if clientes_a_crear:
            logger.info(f"👥 Procesando {len(clientes_a_crear)} clientes...")

            # Separar clientes nuevos de los que necesitan actualización
            clientes_nuevos = []
            clientes_actualizar = []

            for rut, d in clientes_a_crear.items():
                if d.get('es_nuevo', True):
                    # Cliente nuevo
                    clientes_nuevos.append(Cliente(
                        rut=d['rut'],
                        nombre=d['nombre'],
                        correo=d['correo'],
                        telefono='',
                        direccion=''
                    ))
                else:
                    # Cliente existente que necesita actualización
                    cliente_existente = clientes_dict.get(rut)
                    if cliente_existente:
                        clientes_actualizar.append((cliente_existente, d['nombre'], d.get('correo')))

            # Crear nuevos clientes
            if clientes_nuevos:
                Cliente.objects.bulk_create(clientes_nuevos, ignore_conflicts=True)
                logger.info(f"✅ {len(clientes_nuevos)} clientes nuevos creados")

            # Actualizar nombres de clientes existentes
            if clientes_actualizar:
                for cliente, nombre_nuevo, correo_nuevo in clientes_actualizar:
                    cliente.nombre = nombre_nuevo
                    if correo_nuevo and not cliente.correo:
                        cliente.correo = correo_nuevo
                    cliente.save()
                logger.info(f"✅ {len(clientes_actualizar)} clientes actualizados con nombre real")

            clientes_dict.update({c.rut: c for c in Cliente.objects.filter(rut__in=clientes_a_crear.keys())})
            self.stats['clientes_creados'] = len(clientes_nuevos)
            self.stats['clientes_actualizados'] = len(clientes_actualizar)

        # 5. CREAR PRODUCTOS FALTANTES (históricos)
        if productos_a_crear:
            logger.info(f"📦 Creando {len(productos_a_crear)} productos históricos...")
            nuevos_productos = [
                Producto(
                    codigo=d['codigo'],
                    nombre=d['nombre'],
                    descripcion=f"Producto histórico: {d['nombre']}",
                    precio_costo=Decimal('0'),
                    precio_venta=d['precio_venta'] if d['precio_venta'] > 0 else Decimal('0'),
                    stock_actual=0,
                    stock_minimo=0,
                    activo=False
                ) for d in productos_a_crear.values()
            ]
            Producto.objects.bulk_create(nuevos_productos, ignore_conflicts=True)
            productos_dict.update({p.codigo: p for p in Producto.objects.filter(codigo__in=productos_a_crear.keys())})
            self.stats['productos_creados'] = len(productos_a_crear)
            logger.info(f"✅ Productos creados")

        # 6. CREAR VENTAS
        logger.info(f"💳 Creando {len(ventas_dict)} ventas...")
        ventas_objs = []
        ventas_items_map = []  # Para mapear venta -> items

        for key, venta_data in ventas_dict.items():
            cliente = clientes_dict.get(venta_data['cliente_rut'])
            if not cliente:
                continue

            total = sum(item['cantidad'] * item['precio_unitario'] for item in venta_data['items'])
            fecha_venta = venta_data['fecha']
            if hasattr(fecha_venta, 'date'):
                fecha_venta = datetime.combine(fecha_venta.date(), datetime.min.time())

            venta = Venta(
                tipo_documento=venta_data['tipo_documento'] or None,
                numero=venta_data['numero'] or None,
                cliente=cliente,
                fecha=fecha_venta,
                total=total,
                metodo_pago=metodo_pago_default,
                estado=estado_default
            )
            ventas_objs.append(venta)
            ventas_items_map.append(venta_data['items'])

        # Insertar ventas en lotes
        batch_size = 5000
        ventas_creadas = []
        for i in range(0, len(ventas_objs), batch_size):
            batch = ventas_objs[i:i + batch_size]
            created = Venta.objects.bulk_create(batch)
            ventas_creadas.extend(created)
            logger.info(f"  ✓ Ventas insertadas: {len(ventas_creadas)}/{len(ventas_objs)}")

        self.stats['ventas_insertadas'] = len(ventas_creadas)
        logger.info(f"✅ {len(ventas_creadas)} ventas insertadas")

        # 7. CREAR DETALLES
        logger.info(f"📝 Creando detalles de venta...")
        detalles_objs = []

        for venta, items in zip(ventas_creadas, ventas_items_map):
            for item in items:
                producto = productos_dict.get(item['codigo_producto'])
                if not producto:
                    self.stats['productos_no_encontrados'] += 1
                    continue

                subtotal = item['cantidad'] * item['precio_unitario']
                detalles_objs.append(DetalleVenta(
                    venta=venta,
                    producto=producto,
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio_unitario'],
                    subtotal=subtotal
                ))

        # Insertar detalles en lotes
        for i in range(0, len(detalles_objs), batch_size):
            batch = detalles_objs[i:i + batch_size]
            DetalleVenta.objects.bulk_create(batch)
            logger.info(f"  ✓ Detalles insertados: {min(i + batch_size, len(detalles_objs))}/{len(detalles_objs)}")

        self.stats['detalles_insertados'] = len(detalles_objs)
        logger.info(f"✅ {len(detalles_objs)} detalles insertados")
        logger.info(f"📊 RESUMEN: {self.stats['ventas_insertadas']} ventas, {self.stats['detalles_insertados']} detalles")

    def _get_or_create_cliente(self, cliente_id, nombre='', correo=''):
        """
        Obtiene o crea un cliente desde el ID (RUT).
        Si el cliente existe, actualiza su nombre y correo si se proporcionaron.

        Args:
            cliente_id: RUT normalizado (sin puntos ni guión)
            nombre: Nombre del cliente
            correo: Correo del cliente
        """
        try:
            cliente = Cliente.objects.get(rut=cliente_id)

            # Actualizar nombre y correo si se proporcionaron y no están vacíos
            actualizado = False
            if nombre and cliente.nombre != nombre:
                # Solo actualizar si el nombre actual es genérico o vacío
                if cliente.nombre.startswith('Cliente ') or not cliente.nombre:
                    cliente.nombre = nombre
                    actualizado = True

            if correo and (not cliente.correo or cliente.correo != correo):
                cliente.correo = correo
                actualizado = True

            if actualizado:
                cliente.save()
                logger.debug(f"✅ Cliente actualizado: {cliente_id}")

        except Cliente.DoesNotExist:
            cliente = Cliente.objects.create(
                rut=cliente_id,
                nombre=nombre if nombre else f'Cliente {cliente_id}',
                telefono='',
                correo=correo if correo else None,
                direccion=''
            )
            self.stats['clientes_creados'] += 1
            logger.debug(f"✅ Cliente creado: {cliente_id} - {nombre if nombre else 'sin nombre'}")

        return cliente

    def _parse_fecha(self, value):
        """Parsea fechas en diferentes formatos"""
        if pd.isna(value):
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()

        # Si es un número (timestamp de Excel), convertir
        if isinstance(value, (int, float)):
            try:
                # Excel almacena fechas como días desde 1900-01-01
                from datetime import timedelta
                excel_epoch = datetime(1899, 12, 30)
                return excel_epoch + timedelta(days=value)
            except Exception as e:
                logger.warning(f"Error convirtiendo timestamp Excel {value}: {str(e)}")

        # Intentar parsear string
        try:
            date_str = str(value).strip()

            # Formatos comunes
            formatos = [
                '%d/%m/%Y',    # 15/01/2025
                '%d-%m-%Y',    # 15-01-2025
                '%Y-%m-%d',    # 2025-01-15
                '%d/%m/%y',    # 15/01/25
                '%d-%m-%y',    # 15-01-25
                '%Y/%m/%d',    # 2025/01/15
                '%d.%m.%Y',    # 15.01.2025
                '%Y%m%d',      # 20250115
            ]

            for fmt in formatos:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue

            # Intentar con pd.to_datetime (más flexible)
            try:
                fecha = pd.to_datetime(date_str, dayfirst=True)
                return fecha.to_pydatetime()
            except:
                pass

            logger.warning(f"No se pudo parsear fecha: {value} (tipo: {type(value).__name__})")
            return None
        except Exception as e:
            logger.warning(f"Error parseando fecha {value}: {str(e)}")
            return None

    def _clean_string(self, value):
        """Limpia y normaliza strings"""
        if pd.isna(value):
            return ''
        return str(value).strip()

    def _normalize_rut(self, rut_value):
        """
        Normaliza RUT chileno eliminando puntos y guiones.
        Ejemplos:
        - "10.041.575-5" -> "100415755"
        - "12345678-9" -> "123456789"
        - "1.234.567-8" -> "12345678"
        """
        if pd.isna(rut_value):
            return ''

        # Convertir a string y limpiar
        rut_str = str(rut_value).strip()

        # Eliminar puntos, guiones, espacios
        rut_normalized = rut_str.replace('.', '').replace('-', '').replace(' ', '')

        # Convertir a mayúsculas por si tiene 'K'
        rut_normalized = rut_normalized.upper()

        return rut_normalized

    def _parse_precio(self, value):
        """Parsea precios, manejando formato chileno"""
        if pd.isna(value):
            return Decimal('0')

        if isinstance(value, (int, float)):
            return Decimal(str(round(value, 2)))

        # Si es string, limpiar y convertir
        price_str = str(value).strip()
        price_str = price_str.replace('$', '').replace(' ', '')

        # Manejar formato chileno (punto = miles, coma = decimal)
        if ',' in price_str and '.' in price_str:
            # Formato: 1.234,56
            price_str = price_str.replace('.', '').replace(',', '.')
        elif '.' in price_str:
            # Si solo tiene punto, verificar si es separador de miles o decimal
            parts = price_str.split('.')
            if len(parts[-1]) == 3:  # 19.334 = miles
                price_str = price_str.replace('.', '')
        elif ',' in price_str:
            # Solo coma: decimal chileno
            price_str = price_str.replace(',', '.')

        try:
            return Decimal(price_str)
        except:
            logger.warning(f"No se pudo parsear precio: {value}, usando 0")
            return Decimal('0')

    def _parse_int(self, value):
        """Parsea integers"""
        if pd.isna(value):
            return 0

        try:
            return int(float(value))
        except:
            logger.warning(f"No se pudo parsear entero: {value}, usando 0")
            return 0

    def _es_nombre_real(self, nombre):
        """
        Detecta si un nombre de cliente es real o genérico.
        Nombres genéricos:
        - Vacío o solo espacios
        - "Cliente General"
        - "Cliente_XXXX" (formato Cliente_ seguido de números)
        - "Cliente XXXX" (formato Cliente seguido de números)
        """
        if not nombre or not nombre.strip():
            return False

        nombre_upper = nombre.strip().upper()

        # Patrones genéricos
        if nombre_upper == 'CLIENTE GENERAL':
            return False

        # Cliente_XXXX o Cliente XXXX (donde XXXX son números)
        if re.match(r'^CLIENTE[_\s]?\d+$', nombre_upper):
            return False

        # Cliente seguido de RUT (números con puntos y guión)
        if re.match(r'^CLIENTE\s+\d+[\.\-\d]*$', nombre_upper):
            return False

        return True
