from rest_framework import serializers
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
