from rest_framework import serializers
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
import re
from decimal import Decimal
from .models import (
    Cliente, Transaccion, Producto, Proveedor,
    OfertaLaboratorio, SugerenciaCompra, Venta, DetalleVenta,
    ProductoProveedorMapping
)

class ClienteSerializer(serializers.ModelSerializer):
    total_compras = serializers.SerializerMethodField()
    monto_total = serializers.SerializerMethodField()
    ultima_compra = serializers.SerializerMethodField()
    frecuencia = serializers.SerializerMethodField()

    class Meta:
        model = Cliente
        fields = '__all__'

    def validate_nombre(self, value):
        """Solo letras, espacios, acentos y guiones. Sin números ni caracteres especiales peligrosos"""
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío")
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-]+$', value.strip()):
            raise serializers.ValidationError("El nombre solo puede contener letras, espacios y guiones")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("El nombre debe tener al menos 2 caracteres")
        if len(value.strip()) > 100:
            raise serializers.ValidationError("El nombre no puede exceder 100 caracteres")
        return value.strip()

    def validate_correo(self, value):
        """Validación estricta de email"""
        if value and value.strip():
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value.strip()):
                raise serializers.ValidationError("Formato de correo electrónico inválido")
            return value.strip().lower()
        return value

    def validate_telefono(self, value):
        """Solo números, espacios, paréntesis y guiones. Formato chileno +56"""
        if value and value.strip():
            clean_phone = re.sub(r'[\s\-\(\)]', '', value)
            if not re.match(r'^\+?56?[0-9]{8,9}$', clean_phone):
                raise serializers.ValidationError("Formato de teléfono inválido. Use formato chileno: +56912345678")
            return value.strip()
        return value

    def get_total_compras(self, obj):
        # Usar valor anotado si está disponible (más eficiente)
        if hasattr(obj, 'total_ventas'):
            return obj.total_ventas
        if hasattr(obj, 'total_compras') and obj.total_compras is not None:
            return obj.total_compras
        return obj.ventas.filter(estado__codigo='completada').count()

    def get_monto_total(self, obj):
        # Usar valor anotado si está disponible (más eficiente)
        if hasattr(obj, 'monto_total') and obj.monto_total is not None:
            return float(obj.monto_total)
        return sum(venta.total for venta in obj.ventas.filter(estado__codigo='completada'))

    def get_ultima_compra(self, obj):
        # Usar valor anotado si está disponible (más eficiente)
        if hasattr(obj, 'ultima_compra') and obj.ultima_compra is not None:
            return obj.ultima_compra.date() if hasattr(obj.ultima_compra, 'date') else obj.ultima_compra
        ultima = obj.ventas.filter(estado__codigo='completada').order_by('-fecha').first()
        return ultima.fecha.date() if ultima else None

    def get_frecuencia(self, obj):
        total = self.get_total_compras(obj)
        return 'frecuente' if total >= 5 else 'normal'


class TransaccionSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)

    class Meta:
        model = Transaccion
        fields = '__all__'


class ProductoListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar productos con métricas de stock.
    Incluye demanda diaria y días de cobertura calculados desde ventas históricas.
    """
    bajo_stock_simple = serializers.SerializerMethodField()
    proveedor_nombre = serializers.CharField(source='proveedor_principal.nombre', read_only=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    stock_minimo_calculado = serializers.SerializerMethodField()
    metricas_stock = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id', 'codigo', 'nombre', 'descripcion',
            'stock_actual', 'stock_minimo', 'stock_minimo_calculado',
            'precio_costo', 'precio_venta',
            'activo', 'bajo_stock_simple',
            'proveedor_nombre', 'categoria_nombre',
            'fecha_registro', 'metricas_stock'
        ]

    def get_bajo_stock_simple(self, obj):
        """Comparación simple sin ML - usa stock_minimo fijo"""
        return obj.stock_actual < obj.stock_minimo

    def get_stock_minimo_calculado(self, obj):
        """Stock mínimo dinámico calculado con ML"""
        try:
            return obj.stock_minimo_calculado
        except Exception:
            return obj.stock_minimo

    def get_metricas_stock(self, obj):
        """Métricas de demanda diaria y días de cobertura"""
        try:
            return obj.metricas_stock
        except Exception:
            return None


class ProductoSerializer(serializers.ModelSerializer):
    """
    Serializer COMPLETO con cálculos ML.
    SOLO usar para detalle de un producto, NO para listas.
    """
    bajo_stock = serializers.ReadOnlyField()
    stock_minimo_calculado = serializers.ReadOnlyField()  # Stock dinámico ML
    metricas_stock = serializers.ReadOnlyField()

    class Meta:
        model = Producto
        fields = '__all__'

    def validate_codigo(self, value):
        """Código alfanumérico, sin caracteres especiales peligrosos"""
        if not value or not value.strip():
            raise serializers.ValidationError("El código no puede estar vacío")
        if not re.match(r'^[a-zA-Z0-9\-_]+$', value.strip()):
            raise serializers.ValidationError("El código solo puede contener letras, números, guiones y guiones bajos")
        if len(value.strip()) > 50:
            raise serializers.ValidationError("El código no puede exceder 50 caracteres")
        return value.strip().upper()

    def validate_nombre(self, value):
        """Nombre del producto, sin caracteres peligrosos"""
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío")
        # Permitir letras, números, espacios, acentos, paréntesis, guiones y comas
        if not re.match(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\-\(\),\.]+$', value.strip()):
            raise serializers.ValidationError("El nombre contiene caracteres no permitidos")
        if len(value.strip()) > 200:
            raise serializers.ValidationError("El nombre no puede exceder 200 caracteres")
        return value.strip()

    def validate_stock_actual(self, value):
        """Stock debe ser entero positivo"""
        if not isinstance(value, int):
            raise serializers.ValidationError("El stock debe ser un número entero")
        if value < 0:
            raise serializers.ValidationError("El stock no puede ser negativo")
        if value > 1000000:
            raise serializers.ValidationError("El stock no puede exceder 1,000,000 unidades")
        return value

    def validate_stock_minimo(self, value):
        """Stock mínimo debe ser entero positivo"""
        if not isinstance(value, int):
            raise serializers.ValidationError("El stock mínimo debe ser un número entero")
        if value < 0:
            raise serializers.ValidationError("El stock mínimo no puede ser negativo")
        if value > 10000:
            raise serializers.ValidationError("El stock mínimo no puede exceder 10,000 unidades")
        return value

    def validate_precio_unitario(self, value):
        """Precio debe ser decimal positivo"""
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("El precio debe ser un número")
        if Decimal(str(value)) < 0:
            raise serializers.ValidationError("El precio no puede ser negativo")
        if Decimal(str(value)) > Decimal('99999999.99'):
            raise serializers.ValidationError("El precio excede el límite máximo")
        return Decimal(str(value))

    def validate_precio_venta(self, value):
        """Precio de venta debe ser decimal positivo"""
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("El precio de venta debe ser un número")
        if Decimal(str(value)) < 0:
            raise serializers.ValidationError("El precio de venta no puede ser negativo")
        if Decimal(str(value)) > Decimal('99999999.99'):
            raise serializers.ValidationError("El precio de venta excede el límite máximo")
        return Decimal(str(value))

    def validate_precio_costo(self, value):
        """Precio de costo debe ser decimal positivo"""
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("El precio de costo debe ser un número")
        if Decimal(str(value)) < 0:
            raise serializers.ValidationError("El precio de costo no puede ser negativo")
        if Decimal(str(value)) > Decimal('99999999.99'):
            raise serializers.ValidationError("El precio de costo excede el límite máximo")
        return Decimal(str(value))

    def validate(self, data):
        """Validación cruzada: precio_venta >= precio_costo"""
        if 'precio_venta' in data and 'precio_costo' in data:
            if Decimal(str(data['precio_venta'])) < Decimal(str(data['precio_costo'])):
                raise serializers.ValidationError({
                    'precio_venta': 'El precio de venta no puede ser menor que el precio de costo'
                })
        return data


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = '__all__'


class OfertaLaboratorioSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source='producto_catalogo.proveedor.nombre', read_only=True)
    producto_descripcion = serializers.CharField(source='producto_catalogo.descripcion', read_only=True)
    laboratorio_nombre = serializers.CharField(source='laboratorio.nombre', read_only=True)
    ahorro = serializers.ReadOnlyField()

    class Meta:
        model = OfertaLaboratorio
        fields = '__all__'


class OfertaLaboratorioDetalladaSerializer(serializers.ModelSerializer):
    """
    Serializer completo para mostrar ofertas por laboratorio
    con TODOS los campos necesarios en el frontend.
    """
    # Proveedor
    proveedor = serializers.SerializerMethodField()

    # Código producto
    codigo_producto = serializers.CharField(source='producto_catalogo.codigo', read_only=True)

    # Descripción del producto
    descripcion = serializers.CharField(source='producto_catalogo.nombre', read_only=True)

    # Principio activo
    principio_activo = serializers.CharField(source='producto_catalogo.descripcion', read_only=True)

    # Laboratorio (ahora es FK)
    laboratorio = serializers.CharField(source='laboratorio.nombre', read_only=True)

    # Lote (si existe en el producto)
    lote = serializers.SerializerMethodField()

    # Precio (precio_oferta si existe, sino precio_normal)
    precio = serializers.SerializerMethodField()

    # % Descuento
    descuento_porcentaje = serializers.DecimalField(source='descuento', max_digits=5, decimal_places=2, read_only=True)

    # Vigencia (fecha_fin - fecha_inicio)
    vencimiento_vigencia = serializers.SerializerMethodField()

    # Días de vigencia
    dias_vigencia = serializers.SerializerMethodField()

    class Meta:
        model = OfertaLaboratorio
        fields = [
            'id',
            'proveedor',
            'codigo_producto',
            'descripcion',
            'principio_activo',
            'laboratorio',
            'lote',
            'precio',
            'precio_normal',
            'precio_oferta',
            'descuento_porcentaje',
            'fecha_inicio',
            'fecha_fin',
            'vencimiento_vigencia',
            'dias_vigencia',
            'activa'
        ]

    def get_proveedor(self, obj):
        """
        Obtener nombre del PROVEEDOR (quien envía el archivo de ofertas).

        IMPORTANTE:
        - PROVEEDOR: Empresa que envía las ofertas (Mediven, Socofar, etc.)
        - LABORATORIO: Fabricante del producto (3M, Abbott, etc.) - está en obj.laboratorio.nombre

        El proveedor viene de: producto_catalogo.proveedor.nombre
        """
        if obj.producto_catalogo and obj.producto_catalogo.proveedor:
            return obj.producto_catalogo.proveedor.nombre
        return 'Sin proveedor'

    def get_lote(self, obj):
        """Lote del producto (si existe en el modelo)"""
        # Por ahora retornar None, pero puede extenderse si se agrega campo lote
        return None

    def get_precio(self, obj):
        """Precio final (oferta si existe, sino normal)"""
        if obj.precio_oferta and obj.precio_oferta > 0:
            return float(obj.precio_oferta)
        return float(obj.precio_normal)

    def get_vencimiento_vigencia(self, obj):
        """Fecha de vencimiento de la vigencia"""
        return obj.fecha_fin

    def get_dias_vigencia(self, obj):
        """
        Días de vigencia desde hoy.
        - Positivo: días restantes de vigencia
        - Negativo: días desde que venció
        """
        from datetime import date
        if obj.fecha_fin:
            return (obj.fecha_fin - date.today()).days
        return 0


class SugerenciaCompraSerializer(serializers.ModelSerializer):
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    producto_descripcion = serializers.CharField(source='producto.descripcion', read_only=True)
    producto_stock = serializers.IntegerField(source='producto.stock_actual', read_only=True)
    producto_minimo = serializers.IntegerField(source='producto.stock_minimo', read_only=True)

    class Meta:
        model = SugerenciaCompra
        fields = '__all__'


class DetalleVentaSerializer(serializers.ModelSerializer):
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_descripcion = serializers.CharField(source='producto.descripcion', read_only=True)

    class Meta:
        model = DetalleVenta
        fields = ['id', 'venta', 'producto', 'producto_codigo', 'producto_nombre',
                  'producto_descripcion', 'cantidad', 'precio_unitario', 'subtotal']


class VentaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    cliente_rut = serializers.CharField(source='cliente.rut', read_only=True)
    cliente_correo = serializers.EmailField(source='cliente.correo', read_only=True)
    detalles = DetalleVentaSerializer(many=True, read_only=True)

    class Meta:
        model = Venta
        fields = '__all__'


class ProductoProveedorMappingSerializer(serializers.ModelSerializer):
    """Serializer para mapeo producto-proveedor"""
    producto_codigo = serializers.CharField(source='producto_interno.codigo', read_only=True)
    producto_nombre = serializers.CharField(source='producto_interno.nombre', read_only=True)
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    ofertas_activas_count = serializers.SerializerMethodField()

    class Meta:
        model = ProductoProveedorMapping
        fields = [
            'id',
            'producto_interno',
            'producto_codigo',
            'producto_nombre',
            'codigo_proveedor',
            'proveedor',
            'proveedor_nombre',
            'nombre_en_catalogo',
            'activo',
            'confianza',
            'fecha_mapeo',
            'mapeado_por',
            'notas',
            'ofertas_activas_count'
        ]

    def get_ofertas_activas_count(self, obj):
        """Cuenta ofertas activas para este mapeo"""
        return obj.get_ofertas_activas().count()


class ProductoConMappingSerializer(serializers.ModelSerializer):
    """
    Serializer de producto con información de mappings y ofertas.
    Útil para ver qué productos tienen códigos mapeados a proveedores.
    """
    bajo_stock = serializers.ReadOnlyField()
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    mappings = ProductoProveedorMappingSerializer(many=True, read_only=True)
    total_mappings = serializers.SerializerMethodField()
    tiene_ofertas = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id',
            'codigo',
            'nombre',
            'descripcion',
            'categoria',
            'stock_actual',
            'stock_minimo',
            'precio_unitario',
            'precio_venta',
            'precio_costo',
            'proveedor',
            'proveedor_nombre',
            'activo',
            'bajo_stock',
            'mappings',
            'total_mappings',
            'tiene_ofertas'
        ]

    def get_total_mappings(self, obj):
        """Total de mappings activos"""
        return obj.mappings.filter(activo=True).count()

    def get_tiene_ofertas(self, obj):
        """Si algún mapping tiene ofertas activas"""
        for mapping in obj.mappings.filter(activo=True):
            if mapping.get_ofertas_activas().exists():
                return True
        return False
