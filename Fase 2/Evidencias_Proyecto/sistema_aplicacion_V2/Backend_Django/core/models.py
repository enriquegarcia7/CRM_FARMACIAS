from django.db import models
from django.utils import timezone

class Cliente(models.Model):
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True, help_text="RUT del cliente sin puntos ni guión")
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.rut:
            return f"{self.nombre} ({self.rut})"
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

class Categoria(models.Model):
    """
    Categorías de productos farmacéuticos.
    Normalización: Evita duplicación de nombres de categorías.
    """
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    icono = models.CharField(max_length=50, blank=True, help_text="Nombre del icono para UI")
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Laboratorio(models.Model):
    """
    Laboratorios fabricantes de productos farmacéuticos.
    Normalización: Evita duplicación de nombres de laboratorios en ofertas.
    """
    nombre = models.CharField(max_length=200, unique=True)
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True)
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    pais = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Laboratorios"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Inventario físico de productos de la farmacia.
    SOLO productos que realmente existen en el stock.
    Separado de ProductoCatalogo (ofertas de proveedores).
    """
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.CharField(max_length=200, blank=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos_inventario',
        help_text="Categoría del producto"
    )
    stock_actual = models.IntegerField(default=0, help_text="Cantidad física en inventario")
    stock_minimo = models.IntegerField(default=10, help_text="Stock mínimo antes de alerta")
    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Precio de venta al público"
    )
    precio_costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Precio de costo/compra"
    )
    proveedor_principal = models.ForeignKey(
        'Proveedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos_inventario',
        help_text="Proveedor principal de este producto"
    )
    codigo_barras = models.CharField(max_length=100, blank=True, help_text="Código de barras EAN")
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(default=timezone.now)
    fecha_ultima_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto en Inventario"
        verbose_name_plural = "Productos en Inventario"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['codigo'], name='idx_prod_codigo'),
            models.Index(fields=['activo', 'stock_actual'], name='idx_prod_activo_stock'),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    @property
    def bajo_stock(self):
        return self.stock_actual < self.stock_minimo

    @property
    def stock_minimo_dinamico(self):
        """Calcula el stock mínimo dinámico basado en ventas históricas y predicción"""
        from .stock_service import stock_service
        return stock_service.calcular_stock_minimo(self)

    @property
    def metricas_stock(self):
        """Retorna métricas de stock útiles para el frontend"""
        from .stock_service import stock_service
        return stock_service.obtener_metricas_producto(self)


class Proveedor(models.Model):
    """
    Proveedores que suministran productos a la farmacia.
    Ejemplo: Mediven, Socofar, Cruz Verde Distribución, etc.
    """
    nombre = models.CharField(max_length=150, unique=True)
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True)
    contacto = models.CharField(max_length=100, blank=True, help_text="Nombre de contacto")
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)  # ✅ Campo único, eliminamos duplicado "correo"
    direccion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class ProductoCatalogo(models.Model):
    """
    Catálogo de productos que proveedores ofrecen.
    NO es inventario físico, es el catálogo disponible para compra.
    Los productos aquí vienen de ofertas ETL (correos de proveedores).
    """
    codigo = models.CharField(max_length=100, unique=True, db_index=True)
    nombre = models.CharField(max_length=300)
    descripcion = models.TextField(blank=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos_catalogo',
        help_text="Categoría del producto"
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name='productos_catalogo',
        help_text="Proveedor que ofrece este producto"
    )
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(default=timezone.now)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'productos_catalogo'
        verbose_name = "Producto de Catálogo"
        verbose_name_plural = "Productos de Catálogo"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['codigo'], name='idx_cat_codigo'),
            models.Index(fields=['proveedor', 'activo'], name='idx_cat_prov_activo'),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre} ({self.proveedor.nombre})"


class OfertaLaboratorio(models.Model):
    """
    Ofertas de productos de laboratorios.
    Ahora usa ProductoCatalogo (no Producto de inventario).
    """
    producto_catalogo = models.ForeignKey(
        ProductoCatalogo,
        on_delete=models.CASCADE,
        related_name='ofertas',
        null=True,  # Temporal para migración
        blank=True,
        help_text="Producto del catálogo de proveedores"
    )
    laboratorio = models.ForeignKey(
        Laboratorio,
        on_delete=models.CASCADE,
        related_name='ofertas',
        null=True,  # Temporal para migración
        blank=True,
        help_text="Laboratorio fabricante"
    )
    precio_normal = models.DecimalField(max_digits=10, decimal_places=2)
    precio_oferta = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fecha_inicio = models.DateField(db_index=True)
    fecha_fin = models.DateField(db_index=True)
    activa = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ofertas_laboratorio'
        verbose_name_plural = "Ofertas de Laboratorios"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['activa', 'fecha_fin'], name='idx_oferta_activa_fecha'),
            models.Index(fields=['laboratorio', 'activa'], name='idx_oferta_lab_activa'),
            models.Index(fields=['producto_catalogo', 'activa'], name='idx_oferta_prod_activa'),
        ]

    def __str__(self):
        return f"{self.laboratorio.nombre} - {self.producto_catalogo.codigo}"

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
            producto_catalogo__codigo=self.codigo_proveedor,
            producto_catalogo__proveedor=self.proveedor,
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
    tipo_documento = models.CharField(max_length=50, blank=True, null=True, help_text='Tipo de documento (Factura, Boleta, etc)')
    numero = models.CharField(max_length=50, blank=True, null=True, help_text='Número de documento de venta')
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
    hash_unico = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text='Hash MD5 único para detectar duplicados: MD5(numero+cliente_rut+fecha)'
    )

    class Meta:
        verbose_name_plural = "Ventas"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['hash_unico']),
            models.Index(fields=['fecha', 'cliente']),
        ]

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

class VentaHistorica(models.Model):
    """Modelo para ventas históricas (transacciones)"""
    fecha = models.DateField()
    cliente_id = models.IntegerField()
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='ventas')
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'ventas_historicas'
        verbose_name = 'Venta Histórica'
        verbose_name_plural = 'Ventas Históricas'
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['cliente_id']),
            models.Index(fields=['producto', 'fecha']),
        ]
    
    def __str__(self):
        return f"Venta {self.id} - {self.fecha}"