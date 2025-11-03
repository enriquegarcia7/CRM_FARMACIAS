import pandas as pd
import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from core.models import Producto, Proveedor, Categoria

logger = logging.getLogger(__name__)


class ProductExcelParser:
    """
    Parser para archivos Excel de inventario de productos.

    Columnas esperadas en el Excel:
    - CODIGO: Código del producto (interno de la farmacia)
    - PRODUCTO: Nombre del producto
    - PREC UNITARIO: Precio unitario (costo)
    - PREC UNIDADES: Precio por unidades
    - STOCK: Stock actual
    - CÓDIGO DE BARRAS: (opcional)
    - NOMBRE UNIT IVA: Nombre completo con IVA (opcional)

    El principio activo se infiere desde ofertas de proveedores si existe.
    """

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.stats = {
            'insertados': 0,
            'actualizados': 0,
            'errores': []
        }

    def parse_and_load(self):
        """
        Parsea el archivo Excel y carga los productos en la base de datos.
        """
        try:
            # Leer Excel
            df = pd.read_excel(self.file_obj, sheet_name=0)

            logger.info(f"📊 Excel cargado: {len(df)} filas")
            logger.info(f"📋 Columnas encontradas: {list(df.columns)}")

            # Normalizar nombres de columnas (eliminar espacios, mayúsculas)
            df.columns = df.columns.str.strip().str.upper()

            # Mapeo de columnas alternativas
            col_mapping = {
                'PRECIO UNITARIO': 'PREC UNITARIO',
                'PRECIO_UNITARIO': 'PREC UNITARIO',
                'PREC_UNITARIO': 'PREC UNITARIO',
                'PRECIO UNIDADES': 'PREC UNIDADES',
                'PRECIO_UNIDADES': 'PREC UNIDADES',
                'PREC_UNIDADES': 'PREC UNIDADES',
                'CODIGO_BARRAS': 'CÓDIGO DE BARRAS',
                'COD_BARRAS': 'CÓDIGO DE BARRAS',
                'CODIGO DE BARRAS': 'CÓDIGO DE BARRAS',
                'NOMBRE UNIT IVA': 'NOMBRE_UNIT_IVA',
                'NOMBRE_UNIT_IVA': 'NOMBRE_UNIT_IVA'
            }

            # Aplicar mapeo
            for old_name, new_name in col_mapping.items():
                if old_name in df.columns and new_name not in df.columns:
                    df.rename(columns={old_name: new_name}, inplace=True)
                    logger.info(f"🔄 Renombrando columna: {old_name} → {new_name}")

            logger.info(f"📋 Columnas finales después del mapeo: {list(df.columns)}")

            # Mostrar muestra de datos para debug
            if len(df) > 0:
                logger.info(f"🔍 Muestra de primera fila:")
                primera_fila = df.iloc[0]
                for col in df.columns:
                    logger.info(f"  [{col}] = '{primera_fila[col]}'")

            # Validar columnas requeridas
            required_cols = ['CODIGO', 'PRODUCTO']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                raise ValueError(
                    f"❌ Faltan columnas requeridas: {missing_cols}\n"
                    f"📋 Columnas disponibles en el Excel: {list(df.columns)}\n"
                    f"💡 Asegúrate de que tu Excel tenga las columnas: CODIGO, PRODUCTO, PREC UNITARIO, PREC UNIDADES, STOCK"
                )

            # Cargar productos
            self._load_products(df)

            logger.info(f"✅ Productos insertados: {self.stats['insertados']}")
            logger.info(f"🔄 Productos actualizados: {self.stats['actualizados']}")
            if self.stats['errores']:
                logger.warning(f"❌ Errores: {len(self.stats['errores'])}")

            return self.stats

        except Exception as e:
            logger.error(f"❌ Error parseando Excel: {e}")
            self.stats['errores'].append(f"Error general: {str(e)}")
            raise

    @transaction.atomic
    def _load_products(self, df):
        """
        Carga productos en la base de datos.
        ELIMINA todos los productos existentes y carga solo los del Excel actual.

        IMPORTANTE:
        - Limpia completamente la tabla de productos
        - Solo inserta los productos del Excel actual
        - Esto asegura que el inventario sea EXACTAMENTE el del Excel
        """
        # Obtener o crear proveedor genérico
        proveedor_generico, _ = Proveedor.objects.get_or_create(
            nombre='Proveedor Genérico',
            defaults={
                'email': 'generico@proveedor.cl',
                'telefono': '+56900000000',
                'direccion': 'Por confirmar'
            }
        )

        # PASO 1: ELIMINAR todos los productos existentes
        productos_eliminados = Producto.objects.all().count()
        logger.info(f"🗑️ Eliminando {productos_eliminados} productos existentes...")
        Producto.objects.all().delete()
        logger.info("✅ Tabla de productos limpiada completamente")

        # Timestamp de esta carga
        ahora = timezone.now()

        for index, row in df.iterrows():
            try:
                # Extraer datos
                codigo = self._clean_string(row.get('CODIGO', ''))
                if not codigo:
                    self.stats['errores'].append(f"Fila {index + 2}: Código vacío")
                    continue

                # Nombre del producto (columna PRODUCTO)
                nombre = self._clean_string(row.get('PRODUCTO', ''))
                if not nombre:
                    # Fallback a NOMBRE_UNIT_IVA si existe
                    nombre = self._clean_string(row.get('NOMBRE_UNIT_IVA', ''))
                if not nombre:
                    nombre = codigo

                # Descripción (usar NOMBRE_UNIT_IVA como descripción completa si existe)
                descripcion = self._clean_string(row.get('NOMBRE_UNIT_IVA', nombre))

                # Precios
                precio_unitario = self._parse_precio(row.get('PREC UNITARIO', 0))
                precio_venta = self._parse_precio(row.get('PREC UNIDADES', precio_unitario))

                # Stock
                stock_actual = self._parse_int(row.get('STOCK', 0))

                # Código de barras (opcional)
                codigo_barras = self._clean_string(row.get('CÓDIGO DE BARRAS', ''))

                # Obtener categoría General por defecto
                categoria_general, _ = Categoria.objects.get_or_create(
                    nombre='General',
                    defaults={'activa': True}
                )

                # Crear nuevo producto (la tabla fue limpiada, todos son nuevos)
                Producto.objects.create(
                    codigo=codigo,
                    nombre=nombre,
                    descripcion=descripcion,
                    categoria=categoria_general,
                    codigo_barras=codigo_barras,
                    stock_actual=stock_actual,
                    stock_minimo=10,  # Valor por defecto
                    precio_venta=precio_venta,
                    precio_costo=precio_unitario,
                    proveedor_principal=proveedor_generico,
                    activo=True
                )

                self.stats['insertados'] += 1
                logger.debug(f"✅ Insertado: {codigo} - {nombre}")

            except Exception as e:
                error_msg = f"Fila {index + 2}: {str(e)}"
                self.stats['errores'].append(error_msg)
                logger.error(f"❌ {error_msg}")
                continue

    def _inferir_principio_activo(self, codigo, nombre):
        """
        Infiere el principio activo del producto.

        Estrategia:
        1. Buscar en mappings de proveedores existentes
        2. Buscar en ofertas de laboratorios
        3. Extraer del nombre del producto (primera palabra significativa)
        4. Si todo falla, usar el nombre completo como categoría

        Returns: str - Principio activo
        """
        from core.models import OfertaLaboratorio, ProductoProveedorMapping
        import re

        # 1. Buscar en mappings existentes
        mapping = ProductoProveedorMapping.objects.filter(
            codigo_proveedor=codigo,
            activo=True
        ).first()

        if mapping and mapping.producto_interno.categoria:
            categoria = mapping.producto_interno.categoria
            if categoria and categoria != 'Sin clasificar' and len(categoria.strip()) > 0:
                logger.debug(f"✓ Principio activo desde mapping: {categoria}")
                return categoria

        # 2. Buscar en ofertas de laboratorios por código
        oferta = OfertaLaboratorio.objects.filter(
            producto__codigo=codigo,
            activa=True
        ).first()

        if oferta and oferta.producto.descripcion:
            categoria = oferta.producto.descripcion
            if categoria and categoria != 'Sin clasificar' and len(categoria.strip()) > 0:
                logger.debug(f"✓ Principio activo desde ofertas: {categoria}")
                return categoria

        # 3. Extraer del nombre del producto
        if nombre and len(nombre.strip()) > 0:
            # Limpiar el nombre
            nombre_limpio = nombre.strip().upper()

            # Lista expandida de principios activos comunes
            principios_activos = [
                'PARACETAMOL', 'IBUPROFENO', 'AMOXICILINA', 'DICLOFENACO',
                'LOSARTAN', 'ATORVASTATINA', 'METFORMINA', 'OMEPRAZOL',
                'ENALAPRIL', 'SIMVASTATINA', 'ASPIRINA', 'NAPROXENO',
                'CLONAZEPAM', 'LORAZEPAM', 'ALPRAZOLAM', 'FLUOXETINA',
                'SERTRALINA', 'ESCITALOPRAM', 'VENLAFAXINA', 'LEVOTIROXINA',
                'PREDNISONA', 'DEXAMETASONA', 'HIDROCORTISONA', 'RANITIDINA',
                'CIPROFLOXACINO', 'AZITROMICINA', 'CLARITROMICINA', 'CEFALEXINA',
                'SALBUTAMOL', 'MONTELUKAST', 'LORATADINA', 'CETIRIZINA',
                'AMLODIPINO', 'CAPTOPRIL', 'HIDROCLOROTIAZIDA', 'FUROSEMIDA',
                'GLIBENCLAMIDA', 'INSULINA', 'KETOPROFENO', 'MELOXICAM'
            ]

            # Buscar coincidencias exactas
            for pa in principios_activos:
                if pa in nombre_limpio:
                    logger.debug(f"✓ Principio activo inferido del nombre: {pa}")
                    return pa.capitalize()

            # 4. Extraer primera palabra significativa del nombre
            # Remover números, puntos, guiones al inicio
            palabras = re.split(r'[\s\-/,]+', nombre_limpio)
            for palabra in palabras:
                # Filtrar palabras muy cortas, números puros, o palabras comunes
                palabra_limpia = re.sub(r'[^A-Z]', '', palabra)
                if len(palabra_limpia) >= 4 and not palabra_limpia.isdigit():
                    # Verificar que no sea una palabra genérica
                    palabras_excluir = ['TABLETA', 'CAPSULA', 'JARABE', 'COMPRIMIDO',
                                       'INYECTABLE', 'SOLUCION', 'CREMA', 'UNGUENTO',
                                       'SUSPENSION', 'GOTAS', 'AMPOLLA', 'SOBRE']
                    if palabra_limpia not in palabras_excluir:
                        logger.debug(f"✓ Principio activo extraído: {palabra_limpia}")
                        return palabra_limpia.capitalize()

        # 5. Si todo falla, usar nombre completo truncado
        if nombre and len(nombre.strip()) > 0:
            # Tomar primeras 3 palabras del nombre
            palabras = nombre.strip().split()[:3]
            categoria_final = ' '.join(palabras)
            logger.debug(f"⚠ Usando nombre truncado como categoría: {categoria_final}")
            return categoria_final

        # Último recurso
        logger.warning(f"⚠ No se pudo inferir principio activo para código {codigo}")
        return 'Producto genérico'

    def _clean_string(self, value):
        """Limpia y normaliza strings"""
        if pd.isna(value):
            return ''
        return str(value).strip()

    def _parse_precio(self, value):
        """Parsea precios, manejando formato chileno"""
        if pd.isna(value):
            return Decimal('0')

        # Si ya es número
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
