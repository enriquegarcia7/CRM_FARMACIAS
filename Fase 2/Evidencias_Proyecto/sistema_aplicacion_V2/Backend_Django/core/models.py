from django.db import models
from django.utils import timezone

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Transaccion(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='transacciones')
    producto = models.CharField(max_length=120)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()
    proveedor = models.CharField(max_length=100, blank=True, null=True)

    def total(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.producto} ({self.fecha})"


# Nuevos modelos para SmartPharm

class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.CharField(max_length=200, blank=True)
    categoria = models.CharField(max_length=100)
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    proveedor = models.ForeignKey('Proveedor', on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Productos"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    @property
    def bajo_stock(self):
        return self.stock_actual < self.stock_minimo


class Proveedor(models.Model):
    nombre = models.CharField(max_length=150)
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True)
    contacto = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    correo = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nombre


class OfertaLaboratorio(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='ofertas')
    laboratorio = models.CharField(max_length=200)
    precio_normal = models.DecimalField(max_digits=10, decimal_places=2)
    precio_oferta = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ofertas_laboratorio'
        verbose_name_plural = "Ofertas de Laboratorios"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.laboratorio} - {self.producto.codigo}"

    @property
    def ahorro(self):
        return self.precio_normal - self.precio_oferta


class ETLLog(models.Model):
    fecha_ejecucion = models.DateTimeField(auto_now_add=True)
    emails_procesados = models.IntegerField(default=0)
    adjuntos_descargados = models.IntegerField(default=0)
    ofertas_extraidas = models.IntegerField(default=0)
    ofertas_insertadas = models.IntegerField(default=0)
    ofertas_actualizadas = models.IntegerField(default=0)
    errores = models.TextField(blank=True)
    duracion_segundos = models.FloatField(default=0)
    exitoso = models.BooleanField(default=True)

    class Meta:
        db_table = 'etl_logs'
        verbose_name_plural = "ETL Logs"
        ordering = ['-fecha_ejecucion']

    def __str__(self):
        return f"ETL {self.fecha_ejecucion.strftime('%Y-%m-%d %H:%M')}"


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
    confianza_ml = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    fuente_datos = models.CharField(max_length=100, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    procesada = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Sugerencias de Compra"
        ordering = ['-prioridad', '-fecha_creacion']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.descripcion} (x{self.cantidad_sugerida})"


class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='ventas')
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
