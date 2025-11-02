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
    en_inventario_actual = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indica si el producto está en el último Excel de inventario cargado"
    )
    fecha_ultima_carga = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de la última vez que este producto fue incluido en una carga de Excel"
    )
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
    laboratorio = models.CharField(max_length=200, db_index=True)  # Índice para filtros
    precio_normal = models.DecimalField(max_digits=10, decimal_places=2)
    precio_oferta = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fecha_inicio = models.DateField(db_index=True)
    fecha_fin = models.DateField(db_index=True)  # Índice para consultas de vigencia
    activa = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ofertas_laboratorio'
        verbose_name_plural = "Ofertas de Laboratorios"
        ordering = ['-created_at']
        indexes = [
            # Índice para consultas de ofertas vigentes (más usado)
            models.Index(fields=['activa', 'fecha_fin'], name='idx_activa_fecha_fin'),
            # Índice para consultas por laboratorio
            models.Index(fields=['laboratorio', 'activa'], name='idx_lab_activa'),
            # Índice para consultas por producto
            models.Index(fields=['producto', 'activa'], name='idx_prod_activa'),
        ]

    def __str__(self):
        return f"{self.laboratorio} - {self.producto.codigo}"

    @property
    def ahorro(self):
        return self.precio_normal - self.precio_oferta


class ProductoProveedorMapping(models.Model):
    """
    Mapeo entre productos internos y códigos de proveedores.
    Permite vincular el inventario interno con ofertas de diferentes proveedores.

    Ejemplo:
    - Producto interno: codigo="PARA-500", nombre="Paracetamol 500mg"
    - Mapeo 1: codigo_proveedor="7891234567890", proveedor="Mediven"
    - Mapeo 2: codigo_proveedor="SOC-PARA-500", proveedor="Socofar"
    """
    producto_interno = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='mappings',
        help_text="Producto del inventario interno"
    )
    codigo_proveedor = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Código del producto según el proveedor"
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name='producto_mappings',
        help_text="Proveedor que usa este código"
    )
    nombre_en_catalogo = models.CharField(
        max_length=300,
        blank=True,
        help_text="Nombre del producto en el catálogo del proveedor"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Si el mapeo está activo o fue descontinuado"
    )
    confianza = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,
        help_text="Nivel de confianza del mapeo (0-100%). 100% = manual, < 100% = automático"
    )
    fecha_mapeo = models.DateTimeField(auto_now_add=True)
    mapeado_por = models.CharField(
        max_length=50,
        default='manual',
        help_text="Origen del mapeo: 'manual', 'automatico', 'ml'"
    )
    notas = models.TextField(
        blank=True,
        help_text="Notas sobre el mapeo"
    )

    class Meta:
        db_table = 'producto_proveedor_mapping'
        verbose_name = "Mapeo Producto-Proveedor"
        verbose_name_plural = "Mapeos Producto-Proveedor"
        ordering = ['-fecha_mapeo']
        indexes = [
            models.Index(fields=['codigo_proveedor', 'proveedor'], name='idx_codigo_prov'),
            models.Index(fields=['producto_interno', 'activo'], name='idx_prod_int_act'),
        ]
        # Un código de proveedor específico solo puede mapear a UN producto interno
        unique_together = [['codigo_proveedor', 'proveedor']]

    def __str__(self):
        return f"{self.producto_interno.codigo} ↔ {self.codigo_proveedor} ({self.proveedor.nombre})"

    def get_ofertas_activas(self):
        """Obtiene ofertas activas para este código de proveedor"""
        from django.utils import timezone
        today = timezone.now().date()

        return OfertaLaboratorio.objects.filter(
            producto__codigo=self.codigo_proveedor,
            activa=True,
            fecha_fin__gte=today
        )


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
        indexes = [
            models.Index(fields=['-fecha_ejecucion'], name='idx_etl_fecha'),
        ]

    def __str__(self):
        return f"ETL {self.fecha_ejecucion.strftime('%Y-%m-%d %H:%M')}"


class ArchivoProcesado(models.Model):
    """
    Registra archivos procesados por el ETL para evitar reprocesamiento.
    Usa hash SHA256 del contenido para detectar duplicados.
    """
    etl_log = models.ForeignKey(ETLLog, on_delete=models.CASCADE, related_name='archivos_procesados')
    nombre_archivo = models.CharField(max_length=255)
    hash_archivo = models.CharField(max_length=64, db_index=True)  # SHA256
    tamano_bytes = models.BigIntegerField(default=0)
    ofertas_extraidas = models.IntegerField(default=0)
    fecha_procesamiento = models.DateTimeField(auto_now_add=True)
    email_id = models.CharField(max_length=100, blank=True)
    email_subject = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'archivos_procesados'
        verbose_name_plural = "Archivos Procesados"
        ordering = ['-fecha_procesamiento']
        indexes = [
            models.Index(fields=['hash_archivo'], name='idx_hash_archivo'),
            models.Index(fields=['-fecha_procesamiento'], name='idx_fecha_proc'),
        ]
        # Evitar duplicados del mismo archivo en la misma ejecución
        unique_together = [['etl_log', 'hash_archivo']]

    def __str__(self):
        return f"{self.nombre_archivo} ({self.fecha_procesamiento.strftime('%Y-%m-%d %H:%M')})"


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
