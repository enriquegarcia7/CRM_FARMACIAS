from django.contrib import admin
from .models import (
    Cliente, Transaccion, Producto, Proveedor, Categoria, Laboratorio,
    ProductoCatalogo, OfertaLaboratorio, SugerenciaCompra, Venta, DetalleVenta
)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'correo', 'telefono', 'fecha_registro')
    search_fields = ('nombre', 'correo')

@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'producto', 'cantidad', 'precio_unitario', 'fecha', 'proveedor')
    list_filter = ('fecha', 'proveedor')
    search_fields = ('producto', 'cliente__nombre')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion', 'categoria', 'stock_actual', 'stock_minimo', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('codigo', 'descripcion')
    list_editable = ('stock_actual',)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'activa', 'fecha_creacion')
    list_filter = ('activa',)
    search_fields = ('nombre',)

@admin.register(Laboratorio)
class LaboratorioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'pais', 'activo', 'fecha_registro')
    list_filter = ('activo', 'pais')
    search_fields = ('nombre', 'rut')

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'telefono', 'email', 'activo')  # ✅ Cambiado 'correo' a 'email'
    list_filter = ('activo',)
    search_fields = ('nombre', 'rut')

@admin.register(ProductoCatalogo)
class ProductoCatalogoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'proveedor', 'activo')
    list_filter = ('activo', 'proveedor', 'categoria')
    search_fields = ('codigo', 'nombre')

@admin.register(OfertaLaboratorio)
class OfertaLaboratorioAdmin(admin.ModelAdmin):
    list_display = ('laboratorio', 'producto_catalogo', 'precio_oferta', 'descuento', 'fecha_inicio', 'fecha_fin', 'activa')  # ✅ Cambiado 'producto' a 'producto_catalogo'
    list_filter = ('activa', 'laboratorio', 'fecha_inicio')
    search_fields = ('producto_catalogo__nombre', 'laboratorio__nombre')
    date_hierarchy = 'fecha_inicio'

@admin.register(SugerenciaCompra)
class SugerenciaCompraAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad_sugerida', 'prioridad', 'procesada', 'fecha_creacion')
    list_filter = ('tipo', 'prioridad', 'procesada')
    search_fields = ('producto__descripcion', 'razon')
    date_hierarchy = 'fecha_creacion'

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha', 'total', 'metodo_pago', 'estado')
    list_filter = ('estado', 'metodo_pago', 'fecha')
    search_fields = ('cliente__nombre',)
    date_hierarchy = 'fecha'
    inlines = [DetalleVentaInline]
