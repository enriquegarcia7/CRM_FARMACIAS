from rest_framework import serializers
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
import re
from decimal import Decimal
from .models import (
    Cliente, Transaccion, Producto, Proveedor,
    OfertaLaboratorio, SugerenciaCompra, Venta, DetalleVenta
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
        return obj.ventas.filter(estado='completada').count()

    def get_monto_total(self, obj):
        return sum(venta.total for venta in obj.ventas.filter(estado='completada'))

    def get_ultima_compra(self, obj):
        ultima = obj.ventas.filter(estado='completada').order_by('-fecha').first()
        return ultima.fecha.date() if ultima else None

    def get_frecuencia(self, obj):
        total = self.get_total_compras(obj)
        return 'frecuente' if total >= 5 else 'normal'


class TransaccionSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)

    class Meta:
        model = Transaccion
        fields = '__all__'


class ProductoSerializer(serializers.ModelSerializer):
    bajo_stock = serializers.ReadOnlyField()

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
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    producto_descripcion = serializers.CharField(source='producto.descripcion', read_only=True)
    ahorro = serializers.ReadOnlyField()

    class Meta:
        model = OfertaLaboratorio
        fields = '__all__'


class SugerenciaCompraSerializer(serializers.ModelSerializer):
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    producto_descripcion = serializers.CharField(source='producto.descripcion', read_only=True)
    producto_stock = serializers.IntegerField(source='producto.stock_actual', read_only=True)
    producto_minimo = serializers.IntegerField(source='producto.stock_minimo', read_only=True)

    class Meta:
        model = SugerenciaCompra
        fields = '__all__'


class DetalleVentaSerializer(serializers.ModelSerializer):
    producto_descripcion = serializers.CharField(source='producto.descripcion', read_only=True)

    class Meta:
        model = DetalleVenta
        fields = '__all__'


class VentaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    detalles = DetalleVentaSerializer(many=True, read_only=True)

    class Meta:
        model = Venta
        fields = '__all__'
