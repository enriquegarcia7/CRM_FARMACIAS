import pandas as pd
import logging
import hashlib
from decimal import Decimal
from django.db import transaction, IntegrityError
from django.utils import timezone
from datetime import datetime
from core.models import Venta, DetalleVenta, Cliente, Producto
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

            if self.stats['productos_no_encontrados'] > 0:
                logger.warning(f"⚠️ Productos no encontrados: {self.stats['productos_no_encontrados']}")

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
            'RUT': ['RUT', 'CLIENTE RUT', 'CLIENTE_RUT', 'RUT CLIENTE'],
            'CLIENTE_ID': ['CLIENTE_ID', 'CLIENTE ID', 'ID CLIENTE', 'ID_CLIENTE'],
            'NOMBRE_CLIENTE': ['NOMBRE CLIENTE', 'NOMBRE_CLIENTE', 'NOMBRE', 'CLIENTE'],
            'CORREO': ['CORREO', 'EMAIL', 'E-MAIL', 'CORREO ELECTRONICO', 'CORREO ELECTRÓNICO'],
            'NUMERO': ['NUMERO DOCUMENTO', 'NÚMERO DOCUMENTO', 'NUMERO_DOCUMENTO', 'NÚMERO', 'NUMERO', 'NRO', 'N°', 'NUMERO DOC'],
            'TIPO_DOCUMENTO': ['TIPO DOCUMENTO', 'TIPO_DOCUMENTO', 'TIPO'],
            'FECHA': ['FECHA'],
            'FECHA_VENCIMIENTO': ['FECHA VENCIMIENTO', 'FECHA_VENCIMIENTO', 'VENCIMIENTO'],
            'ORDEN_COMPRA': ['ORDEN COMPRA', 'ORDEN_COMPRA', 'OC'],
            'VENDEDOR': ['VENDEDOR'],
            'DISTRIBUIDOR': ['DISTRIBUIDOR'],
            'SUCURSAL': ['SUCURSAL'],
            'CENTRO_COSTO': ['CENTRO COSTO', 'CENTRO_COSTO'],
            'CODIGO': ['CODIGO', 'CÓDIGO', 'COD', 'SKU'],
            'PRODUCTO': ['PRODUCTO', 'DESCRIPCION', 'DESCRIPCIÓN'],
            'CANTIDAD': ['CANTIDAD', 'CANT', 'QTY'],
            'PRECIO_UNITARIO': ['PRECIO', 'PRECIO UNITARIO', 'PRECIO_UNITARIO'],
            'DESCUENTO': ['DESCUENTO'],
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
        Carga ventas en la base de datos con procesamiento optimizado por lotes.

        ESTRATEGIA OPTIMIZADA:
        1. Pre-cargar todos los productos y clientes en memoria (1 consulta cada uno)
        2. Pre-cargar detalles existentes para detectar duplicados (numero_doc + codigo_producto)
        3. Crear clientes faltantes en lote (bulk_create)
        4. Agrupar ventas por FECHA + CLIENTE RUT + NUMERO
        5. Crear ventas en lotes
        6. Crear detalles en lotes (solo los no duplicados)
        """
        logger.info(f"🚀 Iniciando procesamiento optimizado de {len(df)} filas")

        # 1. PRE-CARGAR TODOS LOS PRODUCTOS EN MEMORIA (1 consulta)
        logger.info("📦 Cargando productos en memoria...")
        productos_dict = {p.codigo: p for p in Producto.objects.all()}
        logger.info(f"✅ {len(productos_dict)} productos cargados en memoria")

        # 2. PRE-CARGAR TODOS LOS CLIENTES EN MEMORIA (1 consulta)
        logger.info("👥 Cargando clientes en memoria...")
        clientes_dict = {c.rut: c for c in Cliente.objects.all()}
        logger.info(f"✅ {len(clientes_dict)} clientes cargados en memoria")

        # 3. PRE-CARGAR DETALLES EXISTENTES PARA DETECTAR DUPLICADOS
        # Clave: (numero_documento, codigo_producto) -> existe
        logger.info("🔍 Cargando detalles existentes para detectar duplicados...")
        detalles_existentes = set()
        for detalle in DetalleVenta.objects.select_related('venta', 'producto').only(
            'venta__numero', 'producto__codigo'
        ):
            if detalle.venta.numero and detalle.producto.codigo:
                clave = (str(detalle.venta.numero).strip(), str(detalle.producto.codigo).strip())
                detalles_existentes.add(clave)
        logger.info(f"✅ {len(detalles_existentes)} combinaciones documento-producto existentes")

        # 4. PROCESAR FILAS Y AGRUPAR VENTAS
        ventas_dict = {}  # key: (fecha, cliente_rut, numero_doc) -> lista de items
        clientes_a_crear = {}  # RUT -> datos del cliente
        detalles_duplicados_omitidos = 0  # Contador de detalles duplicados

        logger.info("📝 Procesando filas del Excel...")
        for index, row in df.iterrows():
            try:
                # Extraer fecha
                fecha = self._parse_fecha(row.get('FECHA'))
                if not fecha:
                    self.stats['errores'].append(f"Fila {index + 2}: Fecha inválida")
                    continue

                # Extraer identificador del cliente (priorizar RUT sobre CLIENTE_ID)
                # RUT es el identificador ÚNICO del cliente
                # IMPORTANTE: Normalizar RUT chileno (eliminar puntos y guión)
                cliente_rut = self._normalize_rut(row.get('RUT', ''))
                if not cliente_rut:
                    # Si no hay RUT, intentar con CLIENTE_ID como fallback
                    cliente_rut = self._normalize_rut(row.get('CLIENTE_ID', ''))

                if not cliente_rut:
                    self.stats['errores'].append(f"Fila {index + 2}: RUT o identificador de cliente vacío")
                    continue

                # Extraer nombre y correo del cliente (si existen)
                nombre_cliente = self._clean_string(row.get('NOMBRE_CLIENTE', ''))
                correo_cliente = self._clean_string(row.get('CORREO', ''))

                # Verificar si el cliente ya existe en memoria o en la lista de creación
                if cliente_rut not in clientes_dict and cliente_rut not in clientes_a_crear:
                    clientes_a_crear[cliente_rut] = {
                        'rut': cliente_rut,
                        'nombre': nombre_cliente if nombre_cliente else f'Cliente {cliente_rut}',
                        'correo': correo_cliente if correo_cliente else None
                    }

                # Extraer código producto
                codigo_producto = self._clean_string(row.get('CODIGO', ''))
                if not codigo_producto:
                    self.stats['errores'].append(f"Fila {index + 2}: Código de producto vacío")
                    continue

                # Buscar producto en el diccionario de memoria (sin consulta DB)
                producto = productos_dict.get(codigo_producto)
                if not producto:
                    self.stats['productos_no_encontrados'] += 1
                    self.stats['errores'].append(
                        f"Fila {index + 2}: Producto {codigo_producto} no encontrado en inventario"
                    )
                    continue

                # Extraer cantidad
                cantidad = self._parse_int(row.get('CANTIDAD', 0))
                if cantidad <= 0:
                    self.stats['errores'].append(f"Fila {index + 2}: Cantidad inválida")
                    continue

                # Extraer precio unitario
                precio_unitario = self._parse_precio(row.get('PRECIO_UNITARIO', 0))
                if precio_unitario <= 0:
                    # Intentar calcular desde NETO
                    neto = self._parse_precio(row.get('NETO', 0))
                    if neto > 0 and cantidad > 0:
                        precio_unitario = neto / cantidad
                    else:
                        precio_unitario = producto.precio_venta

                # Número de documento (para agrupar)
                numero_doc = self._clean_string(row.get('NUMERO', ''))

                # VERIFICAR DUPLICADO: si ya existe este documento + producto, omitir
                clave_duplicado = (numero_doc, codigo_producto)
                if numero_doc and clave_duplicado in detalles_existentes:
                    detalles_duplicados_omitidos += 1
                    continue  # Omitir esta fila, ya existe en la BD

                # Agregar a set para evitar duplicados dentro del mismo archivo
                if numero_doc:
                    detalles_existentes.add(clave_duplicado)

                # Agrupar por fecha, cliente RUT y número de documento
                key = (fecha.date(), cliente_rut, numero_doc)
                if key not in ventas_dict:
                    ventas_dict[key] = {
                        'items': [],
                        'tipo_documento': self._clean_string(row.get('TIPO_DOCUMENTO', '')),
                        'fecha_vencimiento': self._parse_fecha(row.get('FECHA_VENCIMIENTO')),
                        'orden_compra': self._clean_string(row.get('ORDEN_COMPRA', '')),
                        'vendedor': self._clean_string(row.get('VENDEDOR', '')),
                        'distribuidor': self._clean_string(row.get('DISTRIBUIDOR', '')),
                        'sucursal': self._clean_string(row.get('SUCURSAL', '')),
                        'centro_costo': self._clean_string(row.get('CENTRO_COSTO', '')),
                    }

                # Agregar item
                descuento = self._parse_precio(row.get('DESCUENTO', 0))
                neto = self._parse_precio(row.get('NETO', 0))
                cuenta = self._clean_string(row.get('CUENTA', ''))
                familia = self._clean_string(row.get('FAMILIA', ''))

                ventas_dict[key]['items'].append({
                    'producto': producto,
                    'producto_nombre': self._clean_string(row.get('PRODUCTO', '')),
                    'cantidad': cantidad,
                    'precio_unitario': precio_unitario,
                    'descuento': descuento,
                    'neto': neto,
                    'cuenta': cuenta,
                    'familia': familia
                })

            except Exception as e:
                error_msg = f"Fila {index + 2}: {str(e)}"
                self.stats['errores'].append(error_msg)
                logger.error(f"❌ {error_msg}")
                continue

        logger.info(f"✅ {len(df)} filas procesadas, {len(ventas_dict)} ventas agrupadas")
        if detalles_duplicados_omitidos > 0:
            logger.info(f"⏭️ {detalles_duplicados_omitidos} filas omitidas (duplicados documento+producto)")
        self.stats['detalles_duplicados_omitidos'] = detalles_duplicados_omitidos

        # 5. CREAR CLIENTES FALTANTES EN LOTE (1 bulk_create)
        if clientes_a_crear:
            logger.info(f"👥 Creando {len(clientes_a_crear)} clientes nuevos...")
            nuevos_clientes = []
            for cliente_data in clientes_a_crear.values():
                nuevos_clientes.append(Cliente(
                    rut=cliente_data['rut'],
                    nombre=cliente_data['nombre'],
                    correo=cliente_data['correo'],
                    telefono='',
                    direccion=''
                ))
            try:
                Cliente.objects.bulk_create(nuevos_clientes, ignore_conflicts=True)
                self.stats['clientes_creados'] = len(nuevos_clientes)
                # Actualizar diccionario de clientes
                clientes_dict.update({c.rut: c for c in Cliente.objects.filter(rut__in=clientes_a_crear.keys())})
                logger.info(f"✅ {len(nuevos_clientes)} clientes creados")
            except Exception as e:
                logger.error(f"❌ Error creando clientes en lote: {e}")

        # 5. CREAR VENTAS Y DETALLES EN LOTES
        logger.info(f"💳 Creando {len(ventas_dict)} ventas...")
        ventas_a_crear = []
        detalles_a_crear = []

        for (fecha, cliente_rut, numero_doc), venta_data in ventas_dict.items():
            try:
                cliente = clientes_dict.get(cliente_rut)

                if not cliente:
                    error_msg = f"Cliente con RUT {cliente_rut} no encontrado en diccionario"
                    self.stats['errores'].append(error_msg)
                    continue

                # Generar hash único para detectar duplicados
                hash_unico = self._generar_hash_venta(numero_doc, cliente_rut, fecha)

                # Calcular total de la venta
                total_venta = sum(
                    item['cantidad'] * item['precio_unitario']
                    for item in venta_data['items']
                )

                # Preparar venta para bulk_create
                venta_obj = Venta(
                    tipo_documento=venta_data['tipo_documento'] if venta_data['tipo_documento'] else None,
                    numero=numero_doc if numero_doc else None,
                    cliente=cliente,
                    fecha=datetime.combine(fecha, datetime.min.time()),
                    total=total_venta,
                    metodo_pago='efectivo',
                    estado='completada',
                    hash_unico=hash_unico
                )
                ventas_a_crear.append((venta_obj, venta_data['items']))

            except Exception as e:
                error_msg = f"Error preparando venta {fecha} - {cliente_rut}: {str(e)}"
                self.stats['errores'].append(error_msg)
                logger.error(f"❌ {error_msg}")

        # 6. CREAR VENTAS EN LOTE (usando ignore_conflicts para duplicados)
        logger.info(f"💾 Insertando {len(ventas_a_crear)} ventas en la BD...")
        if ventas_a_crear:
            try:
                # Extraer solo los objetos Venta (sin los items)
                ventas_objs = [v[0] for v in ventas_a_crear]
                ventas_creadas = Venta.objects.bulk_create(ventas_objs, ignore_conflicts=True)

                # Recuperar las ventas creadas para obtener sus IDs
                hashes_creados = [v.hash_unico for v in ventas_objs if v.hash_unico]
                ventas_bd = {v.hash_unico: v for v in Venta.objects.filter(hash_unico__in=hashes_creados)}

                self.stats['ventas_insertadas'] = len(ventas_bd)
                self.stats['ventas_duplicadas'] = len(ventas_a_crear) - len(ventas_bd)

                logger.info(f"✅ {self.stats['ventas_insertadas']} ventas insertadas, {self.stats['ventas_duplicadas']} duplicadas omitidas")

                # 7. CREAR DETALLES EN LOTE
                logger.info(f"📝 Preparando detalles de venta...")
                for venta_obj, items in ventas_a_crear:
                    venta_bd = ventas_bd.get(venta_obj.hash_unico)
                    if venta_bd:  # Solo crear detalles si la venta fue insertada
                        for item in items:
                            subtotal = item['cantidad'] * item['precio_unitario']
                            # Usar neto del Excel si existe, sino calcular desde precio_unitario
                            neto_valor = item.get('neto')
                            if neto_valor and neto_valor > 0:
                                # Redondear el neto del Excel (sin decimales)
                                neto_redondeado = round(neto_valor)
                            else:
                                # Calcular neto = precio_unitario / 1.19 (redondeado)
                                neto_redondeado = round(float(item['precio_unitario']) / 1.19)

                            detalles_a_crear.append(DetalleVenta(
                                venta=venta_bd,
                                producto=item['producto'],
                                cantidad=item['cantidad'],
                                precio_unitario=item['precio_unitario'],
                                neto=Decimal(str(neto_redondeado)),
                                subtotal=subtotal
                            ))

                # Insertar detalles en lote
                if detalles_a_crear:
                    logger.info(f"💾 Insertando {len(detalles_a_crear)} detalles en la BD...")
                    DetalleVenta.objects.bulk_create(detalles_a_crear, batch_size=5000)
                    self.stats['detalles_insertados'] = len(detalles_a_crear)
                    logger.info(f"✅ {len(detalles_a_crear)} detalles insertados")

            except Exception as e:
                error_msg = f"Error en bulk_create: {str(e)}"
                self.stats['errores'].append(error_msg)
                logger.error(f"❌ {error_msg}")
                import traceback
                traceback.print_exc()

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

        # Intentar parsear string
        try:
            date_str = str(value).strip()

            # Formatos comunes
            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue

            logger.warning(f"No se pudo parsear fecha: {value}")
            return None
        except:
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
