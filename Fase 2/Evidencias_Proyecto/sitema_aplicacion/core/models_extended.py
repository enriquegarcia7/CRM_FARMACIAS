# Modelos extendidos para SmartPharm
# Este archivo contiene los modelos adicionales necesarios
# Para implementar: copiar estos modelos a core/models.py

from django.db import models
from django.utils import timezone

class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=200)
    categoria = models.CharField(max_length=100)
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Productos"

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"

    @property
    def bajo_stock(self):
        return self.stock_actual < self.stock_minimo


class Venta(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, related_name='ventas')
    fecha = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=50, choices=[
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
    ])
    estado = models.CharField(max_length=20, choices=[
        ('completada', 'Completada'),
        ('pendiente', 'Pendiente'),
        ('cancelada', 'Cancelada'),
    ], default='completada')

    class Meta:
        verbose_name_plural = "Ventas"
        ordering = ['-fecha']

    def __str__(self):
        return f"Venta #{self.id} - {self.cliente.nombre} - {self.fecha.date()}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name_plural = "Detalles de Venta"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.descripcion} x {self.cantidad}"


class Proveedor(models.Model):
    nombre = models.CharField(max_length=150)
    rut = models.CharField(max_length=12, unique=True)
    contacto = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    correo = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nombre


class OfertaLaboratorio(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='ofertas')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='ofertas')
    precio_normal = models.DecimalField(max_digits=10, decimal_places=2)
    precio_oferta = models.DecimalField(max_digits=10, decimal_places=2)
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    fecha_vigencia = models.DateField()
    fecha_carga = models.DateTimeField(auto_now_add=True)
    archivo_origen = models.CharField(max_length=255, blank=True)  # Nombre del archivo Excel/PDF
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Ofertas de Laboratorios"
        ordering = ['-fecha_vigencia']

    def __str__(self):
        return f"{self.proveedor.nombre} - {self.producto.descripcion} ({self.descuento_porcentaje}% OFF)"

    @property
    def ahorro(self):
        return self.precio_normal - self.precio_oferta


class SugerenciaCompra(models.Model):
    TIPO_SUGERENCIA = [
        ('bajo_stock', 'Bajo Stock'),
        ('estacional', 'Estacional'),
        ('epidemiologico', 'Epidemiológico'),
        ('ml', 'Machine Learning'),
    ]

    PRIORIDAD = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_SUGERENCIA)
    cantidad_sugerida = models.IntegerField()
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD)
    razon = models.TextField()
    confianza_ml = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)  # 0.00 - 1.00
    fuente_datos = models.CharField(max_length=100, blank=True)  # ej: "MINSAL", "Histórico", etc.
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    procesada = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Sugerencias de Compra"
        ordering = ['-prioridad', '-fecha_creacion']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.descripcion} (x{self.cantidad_sugerida})"


class AlertaEpidemiologica(models.Model):
    enfermedad = models.CharField(max_length=150)
    descripcion = models.TextField()
    nivel_alerta = models.CharField(max_length=20, choices=[
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ])
    fuente = models.CharField(max_length=100, default='MINSAL Chile')
    url_fuente = models.URLField(blank=True)
    fecha_alerta = models.DateField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)
    medicamentos_recomendados = models.ManyToManyField(Producto, related_name='alertas_epidemiologicas')

    class Meta:
        verbose_name_plural = "Alertas Epidemiológicas"
        ordering = ['-fecha_alerta', '-nivel_alerta']

    def __str__(self):
        return f"{self.enfermedad} - {self.get_nivel_alerta_display()}"


class OrdenCompra(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_entrega_estimada = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=[
        ('borrador', 'Borrador'),
        ('enviada', 'Enviada'),
        ('confirmada', 'Confirmada'),
        ('recibida', 'Recibida'),
        ('cancelada', 'Cancelada'),
    ], default='borrador')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Órdenes de Compra"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"OC #{self.id} - {self.proveedor.nombre} - {self.fecha_creacion.date()}"


class DetalleOrdenCompra(models.Model):
    orden = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name_plural = "Detalles de Orden de Compra"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.descripcion} x {self.cantidad}"


class ConfiguracionEmail(models.Model):
    nombre_campana = models.CharField(max_length=100)
    asunto = models.CharField(max_length=200)
    mensaje_html = models.TextField()
    dirigido_a = models.CharField(max_length=20, choices=[
        ('frecuentes', 'Clientes Frecuentes'),
        ('normales', 'Clientes Normales'),
        ('todos', 'Todos'),
        ('custom', 'Personalizado'),
    ])
    minimo_compras = models.IntegerField(default=5, help_text="Mínimo de compras para clientes frecuentes")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=[
        ('borrador', 'Borrador'),
        ('programado', 'Programado'),
        ('enviado', 'Enviado'),
        ('cancelado', 'Cancelado'),
    ], default='borrador')

    class Meta:
        verbose_name_plural = "Configuraciones de Email"

    def __str__(self):
        return f"{self.nombre_campana} - {self.get_estado_display()}"
