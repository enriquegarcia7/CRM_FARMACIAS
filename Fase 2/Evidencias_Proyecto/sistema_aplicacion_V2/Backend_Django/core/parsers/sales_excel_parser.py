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

    Columnas del Excel:
    - TIPO DOCUMENTO
    - NUMERO
    - FECHA
    - FECHA VENCIMIENTO
    - CLIENTE RUT
    - ORDEN COMPRA
    - VENDEDOR
    - DISTRIBUIDOR
    - SUCURSAL
    - CENTRO COSTO
    - CODIGO
    - PRODUCTO
    - CANTIDAD
    - PRECIO UNITARIO
    - DESCUENTO
    - NETO
    - CUENTA
    - FAMILIA

    TODAS se cargan en la BD, pero en la vista solo se muestran:
    - NOMBRE CLIENTE (del modelo Cliente via RUT)
    - RUT (CLIENTE RUT)
    - FECHA COMPRA (FECHA)
    - CODIGO
    - PRODUCTO
    - CANTIDAD
    - PRECIO UNITARIO
    - NETO
    - TOTAL (PRECIO UNITARIO * CANTIDAD)
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
            required_cols = ['FECHA', 'RUT', 'PRODUCTO', 'CANTIDAD', 'PRECIO_UNITARIO']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                raise ValueError(
                    f"❌ No se pudieron mapear las columnas requeridas: {missing_cols}\n"
                    f"📋 Columnas disponibles: {list(df.columns)}\n"
                    f"💡 Verifica que el Excel tenga fecha, RUT/cliente, producto, cantidad y precio"
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
        mappings = {
            'RUT': ['CLIENTE RUT', 'CLIENTE_RUT', 'RUT'],
            'NUMERO': ['NÚMERO', 'NUMERO', 'NRO', 'N°', 'NUMERO DOC', 'NUMERO DOCUMENTO'],
            'TIPO_DOCUMENTO': ['TIPO DOCUMENTO', 'TIPO_DOCUMENTO', 'TIPO'],
            'FECHA': ['FECHA'],
            'FECHA_VENCIMIENTO': ['FECHA VENCIMIENTO', 'FECHA_VENCIMIENTO', 'VENCIMIENTO'],
            'ORDEN_COMPRA': ['ORDEN COMPRA', 'ORDEN_COMPRA', 'OC'],
            'VENDEDOR': ['VENDEDOR'],
            'DISTRIBUIDOR': ['DISTRIBUIDOR'],
            'SUCURSAL': ['SUCURSAL'],
            'CENTRO_COSTO': ['CENTRO COSTO', 'CENTRO_COSTO'],
            'CODIGO': ['CODIGO', 'CÓDIGO', 'COD', 'SKU'],
            'PRODUCTO': ['DESCRIPCION', 'DESCRIPCIÓN', 'PRODUCTO'],
            'CANTIDAD': ['CANTIDAD', 'CANT', 'QTY'],
            'PRECIO_UNITARIO': ['PRECIO UNITARIO', 'PRECIO_UNITARIO', 'PRECIO'],
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
        Carga ventas en la base de datos.

        ESTRATEGIA:
        1. Agrupar por FECHA + CLIENTE RUT + NUMERO (si existe) para crear Ventas
        2. Cada fila del Excel es un DetalleVenta
        3. Guardar TODOS los campos del Excel en campos adicionales
        """
        # Agrupar ventas por fecha, cliente y número de documento
        ventas_dict = {}  # key: (fecha, cliente_rut, numero_doc) -> lista de items

        for index, row in df.iterrows():
            try:
                # Extraer fecha
                fecha = self._parse_fecha(row.get('FECHA'))
                if not fecha:
                    self.stats['errores'].append(f"Fila {index + 2}: Fecha inválida")
                    continue

                # Extraer RUT cliente
                cliente_rut = self._clean_string(row.get('RUT', ''))
                if not cliente_rut:
                    self.stats['errores'].append(f"Fila {index + 2}: RUT cliente vacío")
                    continue

                # Obtener o crear cliente
                cliente = self._get_or_create_cliente(cliente_rut)

                # Extraer código producto
                codigo_producto = self._clean_string(row.get('CODIGO', ''))
                if not codigo_producto:
                    self.stats['errores'].append(f"Fila {index + 2}: Código de producto vacío")
                    continue

                # Buscar producto en inventario
                producto = Producto.objects.filter(codigo=codigo_producto).first()
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

                # Agrupar por fecha, cliente y número de documento
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

        # Crear ventas y detalles
        for (fecha, cliente_rut, numero_doc), venta_data in ventas_dict.items():
            try:
                cliente = Cliente.objects.get(rut=cliente_rut)

                # Generar hash único para detectar duplicados
                hash_unico = self._generar_hash_venta(numero_doc, cliente_rut, fecha)

                # Calcular total de la venta (PRECIO UNITARIO * CANTIDAD para cada item)
                total_venta = sum(
                    item['cantidad'] * item['precio_unitario']
                    for item in venta_data['items']
                )

                # Intentar crear venta (detecta duplicados por hash único)
                try:
                    venta = Venta.objects.create(
                        numero=numero_doc if numero_doc else None,
                        cliente=cliente,
                        fecha=datetime.combine(fecha, datetime.min.time()),
                        total=total_venta,
                        metodo_pago='efectivo',
                        estado='completada',
                        hash_unico=hash_unico
                    )
                    self.stats['ventas_insertadas'] += 1

                    # Crear detalles solo si la venta es nueva
                    for item in venta_data['items']:
                        subtotal = item['cantidad'] * item['precio_unitario']

                        DetalleVenta.objects.create(
                            venta=venta,
                            producto=item['producto'],
                            cantidad=item['cantidad'],
                            precio_unitario=item['precio_unitario'],
                            subtotal=subtotal
                        )
                        self.stats['detalles_insertados'] += 1

                    logger.debug(f"✅ Venta creada: {fecha} - {cliente.nombre} - ${total_venta} ({len(venta_data['items'])} items)")

                except IntegrityError:
                    # Venta duplicada - ya existe en la BD
                    self.stats['ventas_duplicadas'] += 1
                    logger.debug(f"⚠️ Venta duplicada omitida: {numero_doc} - {cliente_rut} - {fecha}")

            except Cliente.DoesNotExist:
                error_msg = f"Cliente con RUT {cliente_rut} no encontrado"
                self.stats['errores'].append(error_msg)
                logger.error(f"❌ {error_msg}")
            except Exception as e:
                error_msg = f"Error creando venta {fecha} - {cliente_rut}: {str(e)}"
                self.stats['errores'].append(error_msg)
                logger.error(f"❌ {error_msg}")

    def _get_or_create_cliente(self, rut):
        """Obtiene o crea un cliente desde el RUT"""
        try:
            cliente = Cliente.objects.get(rut=rut)
        except Cliente.DoesNotExist:
            cliente = Cliente.objects.create(
                rut=rut,
                nombre=f'Cliente {rut}',
                telefono='',
                correo=None,
                direccion=''
            )
            self.stats['clientes_creados'] += 1
            logger.debug(f"✅ Cliente creado: {rut}")

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
