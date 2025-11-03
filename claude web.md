# 📘 DOCUMENTACIÓN COMPLETA SMARTPHARM CRM
**Sistema de Gestión Farmacéutica con ETL Automatizado y Análisis Predictivo**

---

## 📑 INFORMACIÓN DEL DOCUMENTO

| Campo | Valor |
|-------|-------|
| **Fecha de Generación** | 2025-11-01 |
| **Versión** | MVP 1.0 |
| **Repositorio** | https://github.com/enriquegarcia7/CRM_FARMACIAS |
| **Estado** | ✅ En Desarrollo - Proyecto Capstone Duoc UC |
| **Institución** | Duoc UC - Sede Antonio Varas |
| **Programa** | Ingeniería en Informática 2025 |
| **Tipo de Proyecto** | Proyecto de Aplicación de Título (APT) / Capstone |

---

## 📋 TABLA DE CONTENIDOS

1. [🎯 Contexto del Proyecto](#contexto)
2. [💡 Resumen Ejecutivo](#resumen-ejecutivo)
3. [🏗️ Arquitectura del Sistema](#arquitectura)
4. [⚙️ Backend Django - Código Completo](#backend-django)
5. [🎨 Frontend React - Código Completo](#frontend-react)
6. [🐳 Configuración Docker](#docker)
7. [🔄 Flujos de Funcionamiento](#flujos)
8. [🚀 Instalación y Despliegue](#instalacion)
9. [📊 Base de Datos y Modelos](#base-de-datos)
10. [🔐 Autenticación y Seguridad](#seguridad)

---

## 🎯 CONTEXTO DEL PROYECTO

### Propósito Académico

SmartPharm CRM es un **Proyecto Capstone** (Aplicación de Título) desarrollado por estudiantes de Ingeniería en Informática en Duoc UC - Sede Antonio Varas. El proyecto tiene una duración de 10 semanas académicas y combina:

- **70% Propuesta de Negocio**: Análisis financiero, Business Plan y Plan de Gestión de Proyectos PMI
- **30% MVP Técnico**: Desarrollo de software funcional como validación del concepto

### Equipo del Proyecto

| Rol | Nombre | Responsabilidad |
|-----|--------|-----------------|
| 🎯 Líder de Proyecto | Enrique García | Análisis financiero, gestión PMI, coordinación general |
| 📊 Validador de Mercado | Daniel Acevedo | Requerimientos del sector farmacéutico |
| 💻 Desarrollador | Bastian Hartal | MVP técnico, arquitectura, documentación |

### Problemática Identificada

Las farmacias pequeñas en Chile enfrentan desafíos críticos:

1. **❌ Gestión Manual Ineficiente**: Análisis manual de ofertas de laboratorios (Mediven, Socofar, etc.)
2. **📉 Falta de Predicción**: Sin capacidad de anticipar demanda estacional
3. **💊 Control de Inventario Básico**: Sin alertas automáticas de stock bajo
4. **🎯 Fidelización Genérica**: Estrategias de marketing no adaptadas al sector farmacéutico
5. **📧 Información Dispersa**: Ofertas llegan por email sin centralización ni procesamiento

### Solución Propuesta

**SmartPharm CRM** es un sistema CRM especializado para farmacias que automatiza:

1. **📧 ETL Automatizado**: Extracción automática de ofertas desde Gmail (Mediven, Socofar)
2. **🔍 Parseo Inteligente**: Procesamiento de archivos Excel/PDF con detección automática de columnas
3. **📊 Dashboard Analítico**: Visualización en tiempo real de métricas clave
4. **💊 Gestión de Inventario**: Control de stock con alertas automáticas de reposición
5. **🎯 Segmentación de Clientes**: Clasificación por tipo de medicamento (crónico vs agudo)
6. **📈 Análisis Predictivo**: Anticipación de demanda estacional (futuro)

### Validación

- ✅ Acceso a datos históricos reales de farmacias (anonimizados)
- ✅ Validación continua con usuarios del sector farmacéutico
- ✅ Testing con casos de uso reales
- ✅ Correos de prueba de Mediven y Socofar

---

## 💡 RESUMEN EJECUTIVO

### ¿Qué es SmartPharm CRM?

SmartPharm CRM es un sistema integral de gestión farmacéutica diseñado para **automatizar completamente el procesamiento de ofertas de laboratorios**. El sistema:

1. **Conecta con Gmail** usando OAuth 2.0
2. **Busca correos** de proveedores (Mediven, Socofar) con palabras clave (precio, oferta, promoción)
3. **Descarga archivos adjuntos** (Excel, PDF, CSV)
4. **Extrae ofertas** con parsers inteligentes que detectan automáticamente las columnas
5. **Carga en base de datos** PostgreSQL con validación y normalización
6. **Muestra en dashboard** con gráficos y métricas en tiempo real

### Valor del Sistema

**Tiempo Ahorrado:**
- Antes: 2-3 horas/día procesando ofertas manualmente
- Después: 5 minutos para ejecutar ETL automático
- **ROI: 92% de reducción de tiempo**

**Decisiones Basadas en Datos:**
- Comparación automática de precios entre laboratorios
- Identificación de mejores ofertas
- Alertas de stock bajo con sugerencias de compra
- Análisis de patrones de consumo

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Stack Tecnológico Completo

### Stack Tecnológico

**Backend:**
- Django 5.1.4 + Django REST Framework 3.16.1
- PostgreSQL 15
- Celery 5.3.4 + Redis 7
- Google OAuth 2.0 + Gmail API
- Pandas, openpyxl, pdfplumber

**Frontend:**
- React 19.1.1 + Vite 5.4.11
- React Router DOM 7.9.4
- Tailwind CSS 3.4.1
- Axios 1.12.2

**Infraestructura:**
- Docker Compose (6 servicios)
- Gunicorn (3 workers)
- Nginx Alpine

---

## ARQUITECTURA

### Diagrama de Servicios

```
┌────────────────┐     ┌────────────────┐     ┌──────────────┐
│ Frontend React │────▶│ Backend Django │────▶│  PostgreSQL  │
│   (Nginx:80)   │     │    (:8000)     │     │   (:5432)    │
└────────────────┘     └────────────────┘     └──────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              ┌─────▼──────┐    ┌──────▼──────┐
              │ Gmail API  │    │    Redis    │
              │  (OAuth)   │    │   (:6379)   │
              └────────────┘    └──────┬──────┘
                                       │
                              ┌────────┴────────┐
                              │                 │
                       ┌──────▼──────┐  ┌──────▼──────┐
                       │Celery Worker│  │ Celery Beat │
                       │  (Tasks)    │  │ (Scheduler) │
                       └─────────────┘  └─────────────┘
```

### Servicios Docker

1. **db**: PostgreSQL 15 (Base de datos principal)
2. **redis**: Redis 7 (Message broker)
3. **backend**: Django + Gunicorn (API REST)
4. **celery_worker**: Procesamiento asíncrono
5. **celery_beat**: Tareas programadas (ETL cada 3 días)
6. **frontend**: React + Nginx (Interfaz de usuario)

---

## BACKEND DJANGO

### 1. SmartPharm/settings.py

**Función:** Configuración principal de Django - Base de datos, middleware, CORS, Celery, archivos estáticos

**Código Completo:**

```python
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-smartpharm-key')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'backend']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'core',
    'rest_framework',
    'django_celery_beat',
    'django_celery_results',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Servir archivos estáticos
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'SmartPharm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'SmartPharm.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME', default='smartpharm_db'),
        'USER': config('DB_USER', default='smartpharm_user'),
        'PASSWORD': config('DB_PASSWORD', default='123456'),
        'HOST': config('DB_HOST', default='db'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

# WhiteNoise configuration para servir archivos estáticos
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # React dev server
    "http://127.0.0.1:5173",
    "http://localhost",  # Frontend en Docker
    "http://localhost:80",
]

CORS_ALLOW_CREDENTIALS = True

# Celery Configuration
import os
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Santiago'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
```

**Componentes clave:**
- `DATABASES`: Configuración PostgreSQL con credenciales desde `.env`
- `CORS_ALLOWED_ORIGINS`: Permite peticiones desde React dev (5173) y Docker (80)
- `CELERY_*`: Configuración completa de Celery con Redis como broker
- `WhiteNoise`: Sirve archivos estáticos comprimidos en producción
- `MIDDLEWARE`: Incluye CORS, WhiteNoise, sesiones y autenticación

---

### 2. core/models.py

**Función:** Modelos de datos Django - Cliente, Producto, Proveedor, OfertaLaboratorio, ETLLog, Venta, DetalleVenta, SugerenciaCompra

**Código Completo:**

```python
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
```

**Modelos principales:**
- `Cliente`: Información de clientes
- `Producto`: Inventario de medicamentos con código único, stock, precios
- `Proveedor`: Laboratorios y proveedores
- `OfertaLaboratorio`: Ofertas extraídas por el ETL
- `ETLLog`: Registro de ejecuciones ETL con estadísticas
- `Venta` + `DetalleVenta`: Sistema de ventas con detalles
- `SugerenciaCompra`: Sugerencias automáticas de reposición

---

### 3. core/etl/offer_etl.py

**Función:** Lógica principal del proceso ETL - Coordina extracción, transformación y carga de ofertas desde Gmail

**Código Completo:**

```python
import os
import json
import logging
from datetime import datetime
from django.db import transaction
from django.conf import settings
from core.services.gmail_service import GmailService
from core.parsers.excel_parser import ExcelOfferParser
from core.parsers.pdf_parser import PDFOfferParser
from core.models import OfertaLaboratorio, Producto, Proveedor, ETLLog

logger = logging.getLogger(__name__)

class OfferETL:
    def __init__(self):
        self.gmail_service = None
        self.stats = {
            'emails_processed': 0,
            'attachments_downloaded': 0,
            'offers_extracted': 0,
            'offers_inserted': 0,
            'offers_updated': 0,
            'errors': []
        }
        self.progress_file = os.path.join(settings.BASE_DIR, 'etl_progress.json')
        self.total_messages = 0
        self.current_message = 0

    def _update_progress(self, percentage, stage, message=''):
        """Actualiza el archivo de progreso del ETL"""
        try:
            progress_data = {
                'percentage': round(percentage, 1),
                'stage': stage,
                'message': message,
                'stats': self.stats.copy(),
                'timestamp': datetime.now().isoformat()
            }
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f)
            logger.info(f"Progress: {percentage:.1f}% - {stage} - {message}")
        except Exception as e:
            logger.error(f"Error updating progress: {e}")

    def run(self, days_back=5, strict_mode=False):
        logger.info(f"=== Starting ETL (last {days_back} days, strict_mode={strict_mode}) ===")
        start_time = datetime.now()

        try:
            # Inicializar progreso
            self._update_progress(0, 'iniciando', 'Iniciando proceso ETL...')

            # Borrar todas las ofertas existentes antes de cargar nuevas
            self._update_progress(5, 'limpiando', 'Eliminando ofertas antiguas...')
            deleted_count = OfertaLaboratorio.objects.all().count()
            OfertaLaboratorio.objects.all().delete()
            logger.info(f"🗑️ Deleted {deleted_count} old offers from database")

            # Conectar a Gmail
            self._update_progress(10, 'conectando', 'Conectando a Gmail...')
            self.gmail_service = GmailService()

            # Buscar mensajes
            mode_text = "específicos" if strict_mode else "con archivos Excel/PDF"
            self._update_progress(15, 'buscando', f'Buscando correos {mode_text}...')
            messages = self.gmail_service.search_offers_emails(days_back=days_back, strict_mode=strict_mode)

            if not messages:
                logger.warning("No messages found")
                self._update_progress(100, 'completado', 'No se encontraron mensajes')
                self._save_log(start_time, True)
                return self.stats

            self.total_messages = len(messages)
            logger.info(f"Found {self.total_messages} messages")
            self._update_progress(20, 'procesando', f'Procesando {self.total_messages} correos...')

            # Procesar mensajes (20% - 90% del progreso)
            for idx, message in enumerate(messages):
                self.current_message = idx + 1
                # Calcular progreso entre 20% y 90%
                progress = 20 + (70 * (idx + 1) / self.total_messages)
                self._update_progress(
                    progress,
                    'procesando',
                    f'Procesando correo {self.current_message}/{self.total_messages}'
                )
                self._process_message(message['id'])

            # Finalizar
            self._update_progress(95, 'finalizando', 'Guardando resultados...')

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"=== ETL Completed in {duration:.2f}s ===")
            logger.info(f"Emails: {self.stats['emails_processed']}")
            logger.info(f"Attachments: {self.stats['attachments_downloaded']}")
            logger.info(f"Offers extracted: {self.stats['offers_extracted']}")
            logger.info(f"Offers inserted: {self.stats['offers_inserted']}")
            logger.info(f"Offers updated: {self.stats['offers_updated']}")
            logger.info(f"Errors: {len(self.stats['errors'])}")

            self._save_log(start_time, True)

            # Progreso completo
            self._update_progress(
                100,
                'completado',
                f'ETL completado: {self.stats["offers_inserted"]} ofertas insertadas'
            )

            return self.stats

        except Exception as e:
            logger.error(f"Critical ETL error: {e}", exc_info=True)
            self.stats['errors'].append(f"Critical: {str(e)}")
            self._update_progress(0, 'error', f'Error: {str(e)}')
            self._save_log(start_time, False)
            return self.stats

    def _process_message(self, message_id):
        try:
            logger.info(f"Processing message {message_id}")
            attachments = self.gmail_service.get_attachments(message_id)

            if not attachments:
                return

            self.stats['emails_processed'] += 1

            for attachment in attachments:
                self._process_attachment(attachment)

        except Exception as e:
            logger.error(f"Error processing message {message_id}: {e}")
            self.stats['errors'].append(f"Message {message_id}: {str(e)}")

    def _process_attachment(self, attachment):
        filename = attachment['filename']
        file_data = attachment['data']

        try:
            if not self._is_valid_extension(filename):
                return

            logger.info(f"Processing: {filename}")
            self.stats['attachments_downloaded'] += 1

            offers = self._parse_file(filename, file_data, attachment)

            if not offers:
                logger.warning(f"No offers from {filename}")
                return

            self.stats['offers_extracted'] += len(offers)
            self._load_offers(offers)

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            self.stats['errors'].append(f"{filename}: {str(e)}")

    def _is_valid_extension(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        valid = ['.xlsx', '.xls', '.csv', '.pdf']
        return ext in valid

    def _parse_file(self, filename, file_data, metadata):
        ext = os.path.splitext(filename)[1].lower()

        if ext in ['.xlsx', '.xls', '.csv']:
            parser = ExcelOfferParser(file_data, filename, metadata)
        elif ext == '.pdf':
            parser = PDFOfferParser(file_data, filename, metadata)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        return parser.parse()

    @transaction.atomic
    def _load_offers(self, offers):
        for offer_data in offers:
            try:
                proveedor, _ = Proveedor.objects.get_or_create(
                    nombre=offer_data['laboratorio'],
                    defaults={
                        'email': f"{offer_data['laboratorio'].lower().replace(' ', '')}@lab.cl",
                        'telefono': '+56900000000',
                        'direccion': 'Por confirmar'
                    }
                )

                producto = self._get_or_create_producto(offer_data, proveedor)

                # Crear nueva oferta (ya borramos todas las antiguas al inicio)
                oferta = OfertaLaboratorio.objects.create(
                    producto=producto,
                    laboratorio=offer_data['laboratorio'],
                    precio_normal=offer_data['precio_normal'],
                    precio_oferta=offer_data['precio_oferta'],
                    descuento=offer_data['descuento'],
                    fecha_inicio=offer_data['fecha_inicio'],
                    fecha_fin=offer_data['fecha_fin'],
                    activa=offer_data['activa'],
                )

                self.stats['offers_inserted'] += 1
                logger.info(f"✓ Created: {producto.nombre} - {offer_data['laboratorio']}")

            except Exception as e:
                logger.error(f"Error inserting offer: {e}")
                self.stats['errors'].append(f"Offer {offer_data.get('producto', 'Unknown')}: {str(e)}")
                continue

    def _get_or_create_producto(self, offer_data, proveedor):
        if offer_data.get('codigo'):
            try:
                return Producto.objects.get(codigo=offer_data['codigo'])
            except Producto.DoesNotExist:
                pass

        producto_nombre = offer_data['producto']
        try:
            return Producto.objects.get(nombre__iexact=producto_nombre)
        except Producto.DoesNotExist:
            pass

        producto = Producto.objects.create(
            codigo=offer_data.get('codigo') or f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            nombre=producto_nombre,
            descripcion=f"From {offer_data.get('source_file', 'email')}",
            categoria='Medicamento',
            stock_actual=0,
            stock_minimo=10,
            precio_unitario=offer_data['precio_normal'],
            proveedor=proveedor
        )

        logger.info(f"→ Created product: {producto.nombre}")
        return producto

    def _save_log(self, start_time, exitoso):
        try:
            duration = (datetime.now() - start_time).total_seconds()
            ETLLog.objects.create(
                emails_procesados=self.stats['emails_processed'],
                adjuntos_descargados=self.stats['attachments_downloaded'],
                ofertas_extraidas=self.stats['offers_extracted'],
                ofertas_insertadas=self.stats['offers_inserted'],
                ofertas_actualizadas=self.stats['offers_updated'],
                errores='\n'.join(self.stats['errors']),
                duracion_segundos=duration,
                exitoso=exitoso
            )
        except Exception as e:
            logger.error(f"Error saving ETL log: {e}")
```

**Flujo ETL:**
1. Inicializa progreso en `etl_progress.json`
2. Elimina ofertas antiguas (limpieza completa)
3. Conecta a Gmail API
4. Busca correos con adjuntos (validación automática)
5. Procesa cada mensaje y descarga adjuntos
6. Parsea archivos Excel/PDF
7. Extrae ofertas con validación de datos
8. Crea/actualiza Proveedor y Producto si no existen
9. Inserta ofertas en la base de datos
10. Registra estadísticas en ETLLog

---

### 4. core/services/gmail_service.py

**Función:** Servicio de integración con Gmail API - Autenticación OAuth, búsqueda de correos, validación, descarga de adjuntos

**Código Completo:**

```python
import os
import base64
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from django.conf import settings
import logging
from config.secrets import get_gmail_token_path

logger = logging.getLogger(__name__)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Configuración de validación
EXCLUDED_SENDERS = ['proyectosmartpharm2025@gmail.com']
TRUSTED_DOMAINS = ['mediven', 'socofar']  # Dominios confiables (sin @)

# Palabras clave (singular y plural, con y sin tildes)
KEYWORDS = [
    'precio', 'precios',
    'oferta', 'ofertas',
    'laboratorio', 'laboratorios',
    'promocion', 'promoción', 'promociones', 'promociónes',
    'lista', 'listas',
    'descuento', 'descuentos',
    'farmacia', 'farmacias'
]

class GmailService:
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """
        Autentica con Gmail usando el token existente.
        Si no existe token o no es válido, lanza una excepción.
        El usuario debe autenticarse primero usando el flujo web OAuth.
        """
        token_path = get_gmail_token_path(settings.BASE_DIR)

        # Verificar si existe el token
        if not os.path.exists(token_path):
            logger.warning("Gmail token not found. User must authenticate first.")
            raise FileNotFoundError(
                "Gmail no está autenticado. "
                "Por favor, ve a la sección ETL y haz clic en 'Autenticar Gmail' para autorizar el acceso."
            )

        # Cargar credenciales desde el token
        self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # Verificar si el token es válido o necesita refresh
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    logger.info("🔄 Refreshing Gmail token...")
                    self.creds.refresh(Request())

                    # Guardar el token actualizado
                    with open(token_path, 'w') as token:
                        token.write(self.creds.to_json())

                    logger.info("✅ Gmail token refreshed successfully")
                except Exception as e:
                    logger.error(f"Error refreshing token: {e}")
                    # Si falla el refresh, solicitar re-autenticación
                    if os.path.exists(token_path):
                        os.remove(token_path)
                    raise Exception(
                        "Token expirado y no se pudo renovar. "
                        "Por favor, vuelve a autenticar Gmail desde la sección ETL."
                    )
            else:
                # Token inválido sin refresh_token
                logger.warning("Gmail token invalid and no refresh_token available")
                if os.path.exists(token_path):
                    os.remove(token_path)
                raise Exception(
                    "Token de Gmail inválido. "
                    "Por favor, vuelve a autenticar Gmail desde la sección ETL."
                )

        # Construir el servicio de Gmail
        self.service = build('gmail', 'v1', credentials=self.creds)
        logger.info("✅ Gmail authenticated successfully")

    def get_messages(self, query='has:attachment', max_results=50):
        try:
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            messages = results.get('messages', [])
            logger.info(f"📧 Found {len(messages)} messages")
            return messages
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []

    def get_message_detail(self, message_id):
        try:
            return self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {e}")
            return None

    def _extract_sender_email(self, sender_string):
        """Extrae el email del string 'From' que puede tener formato 'Name <email@domain.com>'"""
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender_string)
        return match.group(0).lower() if match else sender_string.lower()

    def _is_excluded_sender(self, sender):
        """Verifica si el remitente está en la lista de excluidos"""
        email = self._extract_sender_email(sender)
        return email in EXCLUDED_SENDERS

    def _is_trusted_domain(self, sender):
        """Verifica si el remitente es de un dominio confiable (Mediven, Socofar)"""
        email = self._extract_sender_email(sender)
        return any(domain in email for domain in TRUSTED_DOMAINS)

    def _contains_keywords(self, text):
        """Verifica si el texto contiene alguna palabra clave (case-insensitive)"""
        if not text:
            return False
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in KEYWORDS)

    def _get_message_body(self, message):
        """Extrae el cuerpo del mensaje (texto plano o HTML)"""
        try:
            payload = message.get('payload', {})
            body = ''

            # Intentar obtener el cuerpo del mensaje
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain' or part.get('mimeType') == 'text/html':
                        data = part.get('body', {}).get('data', '')
                        if data:
                            body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            else:
                # Mensaje simple sin partes
                data = payload.get('body', {}).get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

            return body
        except Exception as e:
            logger.error(f"Error extracting message body: {e}")
            return ''

    def _validate_message(self, message):
        """
        Valida si un mensaje cumple con los criterios:
        1. No debe ser enviado desde proyectosmartpharm2025@gmail.com
        2. Debe ser de dominio confiable (Mediven/Socofar) O contener palabras clave
        """
        try:
            headers = message['payload'].get('headers', [])
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')

            # 1. Excluir si es del remitente excluido
            if self._is_excluded_sender(sender):
                logger.debug(f"✗ Mensaje excluido por remitente: {sender}")
                return False

            # 2. Aceptar si es de dominio confiable
            if self._is_trusted_domain(sender):
                logger.info(f"✓ Mensaje aceptado por dominio confiable: {sender}")
                return True

            # 3. Validar palabras clave en asunto o cuerpo
            if self._contains_keywords(subject):
                logger.info(f"✓ Mensaje aceptado por palabra clave en asunto: {subject}")
                return True

            # Obtener cuerpo del mensaje
            body = self._get_message_body(message)
            if self._contains_keywords(body):
                logger.info(f"✓ Mensaje aceptado por palabra clave en cuerpo")
                return True

            # No cumple criterios
            logger.debug(f"✗ Mensaje rechazado - Sin palabras clave: {subject}")
            return False

        except Exception as e:
            logger.error(f"Error validating message: {e}")
            return False

    def get_attachments(self, message_id):
        attachments = []
        try:
            message = self.get_message_detail(message_id)
            if not message:
                return attachments

            headers = message['payload'].get('headers', [])
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'No Date')

            parts = message['payload'].get('parts', [])
            for part in parts:
                if part.get('filename'):
                    attachment_id = part['body'].get('attachmentId')
                    if attachment_id:
                        attachment = self.service.users().messages().attachments().get(
                            userId='me', messageId=message_id, id=attachment_id
                        ).execute()

                        file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))

                        attachments.append({
                            'filename': part['filename'],
                            'mime_type': part['mimeType'],
                            'size': part['body'].get('size', 0),
                            'data': file_data,
                            'sender': sender,
                            'subject': subject,
                            'date': date,
                            'message_id': message_id
                        })

            logger.info(f"📎 Message {message_id}: {len(attachments)} attachments")
            return attachments
        except Exception as e:
            logger.error(f"Error getting attachments: {e}")
            return []

    def search_offers_emails(self, days_back=3, strict_mode=False):
        """
        Busca correos con ofertas de laboratorios con validación avanzada.

        Args:
            days_back: Número de días hacia atrás para buscar
            strict_mode: No usado actualmente (mantenido por compatibilidad)

        Validaciones aplicadas:
        1. Excluye correos de proyectosmartpharm2025@gmail.com
        2. Acepta correos de dominios Mediven y Socofar
        3. Valida palabras clave en asunto/cuerpo (precio, oferta, laboratorio, etc.)
        """
        # Buscar todos los correos con adjuntos Excel/PDF
        query = (
            f'has:attachment newer_than:{days_back}d '
            f'(filename:xlsx OR filename:xls OR filename:pdf OR filename:csv)'
        )
        logger.info(f"🔍 Searching emails with Excel/PDF attachments from last {days_back} days")

        # Obtener mensajes
        messages = self.get_messages(query=query)
        logger.info(f"📧 Found {len(messages)} messages with attachments")

        # Aplicar validaciones
        validated_messages = []
        for msg in messages:
            # Obtener detalles del mensaje para validación
            message_detail = self.get_message_detail(msg['id'])
            if message_detail and self._validate_message(message_detail):
                validated_messages.append(msg)

        logger.info(f"✅ {len(validated_messages)} messages passed validation")
        logger.info(f"❌ {len(messages) - len(validated_messages)} messages rejected")

        return validated_messages
```

**Funcionalidades clave:**
- `_authenticate()`: Autentica con token OAuth, refresca automáticamente si expira
- `_validate_message()`: Filtra correos (excluye propios, acepta Mediven/Socofar, valida palabras clave)
- `search_offers_emails()`: Busca correos con adjuntos Excel/PDF y aplica validaciones
- `get_attachments()`: Descarga archivos adjuntos con metadata (sender, subject, date)
- Renovación automática de tokens OAuth cuando expiran

---

### 5. core/parsers/excel_parser.py

**Función:** Parser de archivos Excel - Detecta columnas automáticamente, extrae ofertas, maneja múltiples formatos

**Código Completo:**

```python
import pandas as pd
import logging
from decimal import Decimal
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class ExcelOfferParser:
    COLUMN_MAPPINGS = {
        'producto': ['producto', 'medicamento', 'item', 'descripcion', 'nombre'],
        'codigo': ['codigo', 'código', 'sku', 'cod', 'code'],
        'precio_normal': ['precio', 'precio normal', 'pvp', 'valor'],
        'precio_oferta': ['oferta', 'precio oferta', 'promoción', 'descuento'],
        'descuento': ['desc', 'descuento', '%', 'porcentaje'],
        'laboratorio': ['laboratorio', 'lab', 'proveedor', 'marca'],
        'vigencia': ['vigencia', 'válido hasta', 'fecha', 'vencimiento']
    }

    def __init__(self, file_data, filename='unknown.xlsx', metadata=None):
        self.file_data = file_data
        self.filename = filename
        self.metadata = metadata or {}
        self.df = None
        self.offers = []

    def parse(self):
        try:
            if isinstance(self.file_data, bytes):
                self.df = pd.read_excel(self.file_data, engine='openpyxl')
            else:
                self.df = pd.read_excel(self.file_data)

            logger.info(f"📊 Excel: {len(self.df)} rows, {len(self.df.columns)} cols")
            self.df.columns = self.df.columns.str.lower().str.strip()
            column_map = self._detect_columns()

            if not column_map.get('producto'):
                raise ValueError("No 'producto' column detected")

            self.offers = self._extract_offers(column_map)
            logger.info(f"✓ {len(self.offers)} offers from {self.filename}")
            return self.offers
        except Exception as e:
            logger.error(f"Error parsing Excel: {e}")
            raise

    def _detect_columns(self):
        column_map = {}
        for key, variations in self.COLUMN_MAPPINGS.items():
            for col in self.df.columns:
                if any(var in col for var in variations):
                    column_map[key] = col
                    break
        return column_map

    def _extract_offers(self, column_map):
        offers = []
        laboratorio = self._extract_laboratorio()

        for idx, row in self.df.iterrows():
            try:
                producto = str(row.get(column_map.get('producto', ''), '')).strip()
                if not producto or producto.lower() in ['nan', 'none', '']:
                    continue

                codigo = str(row.get(column_map.get('codigo', ''), '')).strip()
                precio_normal = self._parse_price(row.get(column_map.get('precio_normal', '')))
                precio_oferta = self._parse_price(row.get(column_map.get('precio_oferta', '')))

                if precio_oferta == 0 and column_map.get('descuento'):
                    desc_pct = self._parse_percentage(row.get(column_map['descuento']))
                    if desc_pct > 0 and precio_normal > 0:
                        precio_oferta = precio_normal * (1 - desc_pct / 100)

                if precio_normal > 0 and precio_oferta > 0:
                    descuento = ((precio_normal - precio_oferta) / precio_normal) * 100
                else:
                    descuento = 0

                vigencia = self._parse_date(row.get(column_map.get('vigencia', '')))
                if not vigencia:
                    vigencia = datetime.now().date() + timedelta(days=30)

                offers.append({
                    'producto': producto,
                    'codigo': codigo if codigo and codigo != 'nan' else None,
                    'laboratorio': laboratorio,
                    'precio_normal': float(precio_normal),
                    'precio_oferta': float(precio_oferta) if precio_oferta > 0 else float(precio_normal),
                    'descuento': round(descuento, 2),
                    'fecha_inicio': datetime.now().date(),
                    'fecha_fin': vigencia,
                    'activa': True,
                    'source_file': self.filename,
                    'source_email': self.metadata.get('sender', 'Unknown'),
                })
            except Exception as e:
                logger.warning(f"Error row {idx}: {e}")
                continue

        return offers

    def _extract_laboratorio(self):
        sender = self.metadata.get('sender', '')
        if '@' in sender:
            domain = sender.split('@')[1].split('.')[0]
            return domain.title()

        filename_clean = self.filename.lower().replace('.xlsx', '').replace('.xls', '')
        known_labs = ['lab chile', 'medisupply', 'farmalab', 'pharma plus', 'biomed']

        for lab in known_labs:
            if lab in filename_clean:
                return lab.title()

        first_word = filename_clean.split('_')[0].split('-')[0]
        return first_word.title() if first_word else 'Laboratorio Desconocido'

    def _parse_price(self, value):
        if pd.isna(value):
            return 0
        price_str = str(value).strip()
        price_str = re.sub(r'[$\s]', '', price_str)
        price_str = price_str.replace('.', '').replace(',', '.')
        try:
            return Decimal(price_str)
        except:
            return 0

    def _parse_percentage(self, value):
        if pd.isna(value):
            return 0
        pct_str = str(value).replace('%', '').strip()
        try:
            return float(pct_str)
        except:
            return 0

    def _parse_date(self, value):
        if pd.isna(value) or not value:
            return None
        if isinstance(value, datetime):
            return value.date()
        date_str = str(value).strip()
        formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d.%m.%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        return None
```

**Capacidades:**
- Detecta automáticamente columnas (producto, precio, descuento, vigencia, etc.)
- Maneja múltiples variaciones de nombres de columnas
- Parsea precios con diferentes formatos ($, puntos, comas)
- Calcula descuentos automáticamente si no están presentes
- Extrae laboratorio desde remitente o nombre de archivo
- Valida y normaliza fechas en múltiples formatos

---

## FRONTEND REACT

### 6. Frontend_React/src/pages/ETL/ETL.jsx

**Función:** Interfaz principal del ETL - Ejecuta ETL manualmente, muestra progreso en tiempo real, historial de ejecuciones

**Código Completo:**

```jsx
import { useState, useEffect } from 'react';
import { etlService, gmailAuthService } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

function ETL() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [gmailAuthenticated, setGmailAuthenticated] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [progress, setProgress] = useState(null);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    loadData();
    checkGmailAuth();
  }, []);

  // Polling para progreso del ETL
  useEffect(() => {
    let intervalId;

    if (isRunning) {
      // Poll cada 500ms para actualizaciones en tiempo real
      intervalId = setInterval(async () => {
        try {
          const response = await etlService.getProgress();
          if (response.data.success) {
            if (response.data.running && response.data.progress) {
              setProgress(response.data.progress);
            } else {
              // ETL terminó
              setIsRunning(false);
              setProgress(response.data.progress);
              setLoading(false);

              // Recargar datos después de completar
              setTimeout(() => {
                loadData();
                setProgress(null);
              }, 3000);
            }
          }
        } catch (err) {
          console.error('Error checking progress:', err);
        }
      }, 500);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isRunning]);

  const checkGmailAuth = async () => {
    try {
      setCheckingAuth(true);
      const response = await gmailAuthService.checkStatus();
      setGmailAuthenticated(response.data.authenticated);
    } catch (err) {
      console.error('Error checking Gmail auth:', err);
      setGmailAuthenticated(false);
    } finally {
      setCheckingAuth(false);
    }
  };

  const loadData = async () => {
    try {
      const [logsRes, statusRes] = await Promise.all([
        etlService.getLogs(),
        etlService.getStatus()
      ]);
      setLogs(logsRes.data.data || []);
      setStatus(statusRes.data.last_execution);
    } catch (err) {
      console.error('Error loading ETL data:', err);
    }
  };

  const handleRunETL = async () => {
    // Verificar autenticación antes de ejecutar
    if (!gmailAuthenticated) {
      setError('Debes autenticar Gmail primero antes de ejecutar el ETL.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccessMessage('');
      setProgress(null);

      // Usar modo amplio (strict_mode=false) para buscar todos los correos con Excel/PDF
      const response = await etlService.runManual(5, false);

      if (response.data.success) {
        setSuccessMessage('✓ ETL iniciado. Buscando correos de Mediven/Socofar y mensajes con palabras clave (últimos 5 días)...');
        setIsRunning(true); // Iniciar polling de progreso
      }
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Error al ejecutar ETL';
      setError(errorMsg);
      setLoading(false);

      // Si el error es por falta de autenticación, actualizar estado
      if (errorMsg.includes('autenticado') || errorMsg.includes('Gmail')) {
        setGmailAuthenticated(false);
      }
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Sistema ETL</h1>
        <p className="text-gray-600">Descarga y procesa ofertas de laboratorios desde Gmail</p>
      </div>

      {/* Estado de Autenticación Gmail */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Autenticación de Gmail</h2>

        {checkingAuth ? (
          <div className="flex items-center text-gray-600">
            <svg className="animate-spin h-5 w-5 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Verificando autenticación...
          </div>
        ) : gmailAuthenticated ? (
          <div className="flex items-center">
            <div className="flex-1">
              <div className="flex items-center text-green-600 mb-2">
                <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="font-semibold">Gmail autenticado correctamente</span>
              </div>
              <p className="text-sm text-gray-600">
                El sistema tiene acceso para leer correos de Gmail.
                <span className="block mt-1 text-xs text-gray-500">
                  ✓ Gmail se autorizó automáticamente al iniciar sesión con Google
                </span>
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center text-red-600 mb-2">
              <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span className="font-semibold">Error de autenticación</span>
            </div>
            <p className="text-sm text-red-700 mb-2">
              Gmail no está autenticado. Por favor, cierra sesión y vuelve a iniciar sesión para autorizar Gmail automáticamente.
            </p>
            <p className="text-xs text-red-600">
              La autenticación de Gmail se realiza automáticamente al iniciar sesión con Google.
            </p>
          </div>
        )}
      </div>

      {/* Botón principal */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Ejecutar ETL Manualmente</h2>
        <p className="text-gray-600 mb-4">
          Busca correos de Mediven/Socofar y mensajes con palabras clave de ofertas de los últimos 5 días.
          Los archivos Excel/PDF adjuntos se procesan y las ofertas se cargan en la base de datos.
        </p>

        <button
          onClick={handleRunETL}
          disabled={loading || !gmailAuthenticated}
          className={`px-6 py-3 rounded-lg font-semibold text-white transition-colors ${
            loading || !gmailAuthenticated
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {loading ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Ejecutando ETL...
            </span>
          ) : (
            '🚀 Ejecutar ETL y Actualizar Precios'
          )}
        </button>

        {!gmailAuthenticated && !checkingAuth && (
          <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-800 font-semibold mb-2">⚠️ Debes autenticar Gmail antes de ejecutar el ETL</p>
            <p className="text-yellow-700 text-sm mt-2">
              💡 <strong>Importante:</strong> Se abrirá una ventana emergente con la autenticación de Google.
              Si no aparece, verifica que tu navegador permite ventanas emergentes para este sitio.
            </p>
          </div>
        )}

        {/* Barra de progreso en tiempo real */}
        {progress && isRunning && (
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-blue-900 font-semibold text-sm">Progreso del ETL</p>
                <p className="text-blue-700 text-xs">{progress.message}</p>
              </div>
              <div className="text-2xl font-bold text-blue-600">
                {progress.percentage}%
              </div>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-4 overflow-hidden">
              <div
                className="bg-blue-600 h-4 transition-all duration-300 ease-out flex items-center justify-end pr-2"
                style={{ width: `${progress.percentage}%` }}
              >
                <span className="text-xs text-white font-medium">
                  {progress.percentage >= 10 && `${progress.percentage}%`}
                </span>
              </div>
            </div>
            <div className="mt-3 grid grid-cols-4 gap-2 text-xs">
              <div className="text-center">
                <p className="text-gray-600">Correos</p>
                <p className="font-semibold text-blue-900">{progress.stats?.emails_processed || 0}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-600">Adjuntos</p>
                <p className="font-semibold text-blue-900">{progress.stats?.attachments_downloaded || 0}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-600">Extraídas</p>
                <p className="font-semibold text-blue-900">{progress.stats?.offers_extracted || 0}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-600">Insertadas</p>
                <p className="font-semibold text-green-600">{progress.stats?.offers_inserted || 0}</p>
              </div>
            </div>
          </div>
        )}

        {/* Mensaje de éxito al completar */}
        {progress && !isRunning && progress.stage === 'completado' && (
          <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <svg className="h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <p className="text-green-800 font-semibold">ETL completado exitosamente</p>
            </div>
            <p className="text-green-700 text-sm mt-1">{progress.message}</p>
          </div>
        )}

        {successMessage && !progress && (
          <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-800">{successMessage}</p>
          </div>
        )}

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">❌ {error}</p>
          </div>
        )}
      </div>

      {/* Estado último ETL */}
      {status && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Última Ejecución</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600">Fecha</p>
              <p className="text-lg font-semibold">
                {new Date(status.fecha).toLocaleString('es-CL')}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Estado</p>
              <p className={`text-lg font-semibold ${status.exitoso ? 'text-green-600' : 'text-red-600'}`}>
                {status.exitoso ? '✓ Exitoso' : '✗ Falló'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Ofertas Insertadas</p>
              <p className="text-lg font-semibold text-blue-600">{status.ofertas_insertadas}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Duración</p>
              <p className="text-lg font-semibold">{status.duracion_segundos.toFixed(1)}s</p>
            </div>
          </div>
        </div>
      )}

      {/* Historial */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Historial de Ejecuciones</h2>

        {logs.length === 0 ? (
          <p className="text-gray-500">No hay registros de ejecuciones anteriores</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Fecha</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Estado</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Emails</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Adjuntos</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Extraídas</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Insertadas</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Duración</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2 text-sm">
                      {new Date(log.fecha_ejecucion).toLocaleString('es-CL')}
                    </td>
                    <td className="px-4 py-2 text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        log.exitoso ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {log.exitoso ? 'Exitoso' : 'Falló'}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-sm">{log.emails_procesados}</td>
                    <td className="px-4 py-2 text-sm">{log.adjuntos_descargados}</td>
                    <td className="px-4 py-2 text-sm">{log.ofertas_extraidas}</td>
                    <td className="px-4 py-2 text-sm text-blue-600 font-semibold">{log.ofertas_insertadas}</td>
                    <td className="px-4 py-2 text-sm">{log.duracion_segundos.toFixed(1)}s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Información adicional */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">ℹ️ Criterios de Validación</h3>
        <div className="space-y-3">
          <div>
            <p className="font-semibold text-blue-900 mb-1">📧 Búsqueda de correos:</p>
            <ul className="list-disc list-inside text-blue-800 text-sm space-y-1 ml-4">
              <li>Busca correos de los últimos 5 días con adjuntos Excel/PDF</li>
              <li>Formatos aceptados: .xlsx, .xls, .csv, .pdf</li>
            </ul>
          </div>

          <div>
            <p className="font-semibold text-blue-900 mb-1">✅ Correos aceptados:</p>
            <ul className="list-disc list-inside text-blue-800 text-sm space-y-1 ml-4">
              <li><strong>Dominios confiables:</strong> Mediven, Socofar (siempre se aceptan)</li>
              <li><strong>Palabras clave en asunto/cuerpo:</strong> Precio, Oferta, Laboratorio, Promoción, Lista, Descuento, Farmacia (singular/plural, mayúsculas/minúsculas)</li>
            </ul>
          </div>

          <div>
            <p className="font-semibold text-blue-900 mb-1">❌ Correos excluidos:</p>
            <ul className="list-disc list-inside text-blue-800 text-sm space-y-1 ml-4">
              <li>Correos enviados desde proyectosmartpharm2025@gmail.com</li>
              <li>Correos sin palabras clave ni de dominios confiables</li>
            </ul>
          </div>

          <div>
            <p className="font-semibold text-blue-900 mb-1">🔄 Proceso:</p>
            <ul className="list-disc list-inside text-blue-800 text-sm space-y-1 ml-4">
              <li>Extrae ofertas de los archivos validados</li>
              <li>Reescribe completamente la base de datos (elimina ofertas antiguas)</li>
              <li>Gmail se autoriza automáticamente al iniciar sesión</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ETL;
```

**Características:**
- Polling de progreso en tiempo real cada 500ms
- Barra de progreso visual con estadísticas (correos, adjuntos, ofertas)
- Verificación de autenticación Gmail antes de ejecutar
- Historial de ejecuciones con filtros
- Mensajes de error y éxito dinámicos
- Documentación de criterios de validación incorporada

---

## DOCKER

### 7. docker-compose.yml

**Función:** Orquestación de 6 servicios Docker - PostgreSQL, Redis, Backend, Celery Worker, Celery Beat, Frontend

**Código Completo:**

```yaml
services:
  # Base de datos PostgreSQL
  db:
    image: postgres:15-alpine
    container_name: smartpharm_db
    env_file:
      - .env
    environment:
      POSTGRES_DB: ${DB_NAME:-smartpharm_db}
      POSTGRES_USER: ${DB_USER:-smartpharm_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-123456}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    networks:
      - smartpharm_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U smartpharm_user -d smartpharm_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend Django
  backend:
    build:
      context: ./Backend_Django
      dockerfile: Dockerfile
    container_name: smartpharm_backend
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('bhartal', 'bastianhartal@gmail.com', '123456') if not User.objects.filter(username='bhartal').exists() else print('Superuser bhartal already exists')\" &&
             gunicorn --bind 0.0.0.0:8000 --workers 3 SmartPharm.wsgi:application"
    volumes:
      # Volumen habilitado para acceder a gmail_credentials.json
      - ./Backend_Django:/app
      - static_volume:/app/staticfiles
    ports:
      - "${BACKEND_PORT:-8000}:8000"
    env_file:
      - .env
    environment:
      - DB_HOST=db
      - DB_NAME=smartpharm_db
      - DB_USER=smartpharm_user
      - DB_PASSWORD=123456
    depends_on:
      db:
        condition: service_healthy
    networks:
      - smartpharm_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis para Celery
  redis:
    image: redis:7-alpine
    container_name: smartpharm_redis
    ports:
      - "6379:6379"
    networks:
      - smartpharm_network
    restart: unless-stopped

  # Celery Worker
  celery_worker:
    build:
      context: ./Backend_Django
      dockerfile: Dockerfile
    container_name: smartpharm_celery_worker
    command: celery -A SmartPharm worker -l info
    volumes:
      - ./Backend_Django:/app
    depends_on:
      - db
      - redis
    environment:
      - DB_HOST=db
      - DB_NAME=smartpharm_db
      - DB_USER=smartpharm_user
      - DB_PASSWORD=123456
      - REDIS_URL=redis://redis:6379/0
    networks:
      - smartpharm_network
    restart: unless-stopped

  # Celery Beat
  celery_beat:
    build:
      context: ./Backend_Django
      dockerfile: Dockerfile
    container_name: smartpharm_celery_beat
    command: celery -A SmartPharm beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - ./Backend_Django:/app
    depends_on:
      - db
      - redis
      - celery_worker
    environment:
      - DB_HOST=db
      - DB_NAME=smartpharm_db
      - DB_USER=smartpharm_user
      - DB_PASSWORD=123456
      - REDIS_URL=redis://redis:6379/0
    networks:
      - smartpharm_network
    restart: unless-stopped

  # Frontend React
  frontend:
    build:
      context: ./Frontend_React
      dockerfile: Dockerfile
    container_name: smartpharm_frontend
    ports:
      - "${FRONTEND_PORT:-80}:80"
    depends_on:
      - backend
    networks:
      - smartpharm_network
    env_file:
      - .env
    environment:
      - VITE_API_URL=${VITE_API_URL:-http://localhost:8000}

volumes:
  postgres_data:
  static_volume:

networks:
  smartpharm_network:
    driver: bridge
```

**Servicios configurados:**
- PostgreSQL con healthcheck y persistencia de datos
- Backend con migraciones automáticas y creación de superusuario
- Celery Worker para procesamiento asíncrono
- Celery Beat para tareas programadas (ETL cada 3 días)
- Frontend Nginx sirviendo React build
- Red bridge compartida para comunicación entre servicios

---

## FLUJOS

### Flujo de Login Completo

1. Usuario hace clic en "Continuar con Google"
2. Frontend llama `GET /api/auth/login/start/`
3. Backend genera URL OAuth con scopes: `openid`, `userinfo`, `gmail.readonly`
4. Se abre popup con autorización de Google
5. Usuario autoriza (login + Gmail automático)
6. Google redirige a `/api/auth/callback?code=...`
7. Backend intercambia code por tokens
8. Backend guarda `user_session_token.json` + `gmail_token.json`
9. Backend retorna HTML con postMessage y localStorage
10. Frontend detecta login mediante polling `/api/auth/session/`
11. Redirección automática a dashboard

### Flujo ETL Completo

1. Usuario autenticado navega a `/etl`
2. Frontend verifica Gmail autenticado
3. Click en "Ejecutar ETL"
4. Frontend `POST /api/etl/run/` (days_back=5, strict_mode=false)
5. Backend crea tarea Celery asíncrona
6. Frontend inicia polling `/api/etl/progress/` cada 500ms
7. Celery Worker ejecuta `OfferETL.run()`:
   - Conecta a Gmail API con token OAuth
   - Busca correos con adjuntos Excel/PDF (últimos 5 días)
   - Valida cada correo (excluye propios, acepta Mediven/Socofar, verifica palabras clave)
   - Descarga archivos adjuntos
   - Parsea con `ExcelOfferParser` o `PDFOfferParser`
   - Elimina todas las ofertas antiguas
   - Crea/actualiza `Producto` y `Proveedor` si no existen
   - Inserta nuevas ofertas en `OfertaLaboratorio`
   - Actualiza `etl_progress.json` cada paso (0% → 100%)
8. Frontend muestra barra de progreso en tiempo real
9. Al completar (100%), registra en `ETLLog`
10. Frontend recarga datos y muestra estadísticas finales

---

## INSTALACIÓN Y DESPLIEGUE

### Requisitos
- Docker 27.x
- Docker Compose 2.x
- Git

### Pasos de Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/enriquegarcia7/CRM_FARMACIAS.git
cd CRM_FARMACIAS

# 2. Navegar al proyecto
cd "Fase 2/Evidencias_Proyecto/sistema_aplicacion_V2"

# 3. Crear archivo .env (opcional, usa defaults si no existe)
cat > .env << EOF
DB_NAME=smartpharm_db
DB_USER=smartpharm_user
DB_PASSWORD=123456
REDIS_URL=redis://redis:6379/0
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback
VITE_API_URL=http://localhost:8000
EOF

# 4. Levantar servicios
docker-compose up -d

# 5. Verificar logs
docker-compose logs -f

# 6. Acceder al sistema
# Frontend: http://localhost
# Backend API: http://localhost:8000
# Admin: http://localhost:8000/admin (bhartal / 123456)
```

### Credenciales por Defecto

**Superusuario Django:**
- Usuario: `bhartal`
- Contraseña: `123456`
- Email: `bastianhartal@gmail.com`

**Base de Datos:**
- Host: `db` (dentro de Docker) / `localhost:5432` (externo)
- Database: `smartpharm_db`
- Usuario: `smartpharm_user`
- Contraseña: `123456`

### Comandos Útiles

```bash
# Ver logs del backend
docker-compose logs -f backend

# Ver logs de Celery Worker
docker-compose logs -f celery_worker

# Ejecutar migraciones manualmente
docker-compose exec backend python manage.py migrate

# Crear superusuario adicional
docker-compose exec backend python manage.py createsuperuser

# Reiniciar servicios
docker-compose restart

# Detener todo
docker-compose down

# Eliminar volúmenes (CUIDADO: borra la base de datos)
docker-compose down -v
```

---

## ENDPOINTS API

### Autenticación
- `GET /api/auth/login/start/` - Iniciar OAuth con Google
- `GET /api/auth/callback` - Callback OAuth
- `GET /api/auth/session/` - Verificar sesión activa
- `POST /api/auth/logout/` - Cerrar sesión

### ETL
- `POST /api/etl/run/` - Ejecutar ETL manual
- `GET /api/etl/logs/` - Historial de ejecuciones
- `GET /api/etl/status/` - Estado última ejecución
- `GET /api/etl/progress/` - Progreso en tiempo real

### CRUD
- `/api/clientes/` - Gestión de clientes
- `/api/productos/` - Gestión de productos
- `/api/proveedores/` - Gestión de proveedores
- `/api/ofertas/` - Gestión de ofertas
- `/api/ventas/` - Gestión de ventas

---

---

## 🔑 INFORMACIÓN CLAVE PARA IAs

### Resumen Ultra-Rápido (Para Contexto Inmediato)

**SmartPharm CRM** es un sistema Django + React + PostgreSQL que:
1. Conecta con Gmail vía OAuth
2. Busca correos de laboratorios (Mediven, Socofar)
3. Descarga Excel/PDF adjuntos
4. Extrae ofertas automáticamente
5. Carga en base de datos
6. Muestra en dashboard React

**Tecnologías Core:**
- Backend: Django 5.1 + DRF + Celery + Redis
- Frontend: React 19 + Vite + TailwindCSS
- DB: PostgreSQL 15
- Infraestructura: Docker Compose (6 servicios)

**Proyecto Académico:** Capstone Duoc UC 2025 | Ingeniería en Informática

---

## 📂 ESTRUCTURA DE DIRECTORIOS

```
Smartpharm_V2/
├── Fase 2/
│   └── Evidencias_Proyecto/
│       └── sistema_aplicacion_V2/           # ← APLICACIÓN PRINCIPAL
│           ├── Backend_Django/              # API REST Django
│           │   ├── core/                    # App principal
│           │   │   ├── models.py           # 8 modelos (Cliente, Producto, OfertaLaboratorio, etc.)
│           │   │   ├── etl/
│           │   │   │   └── offer_etl.py    # ⭐ Lógica ETL principal
│           │   │   ├── services/
│           │   │   │   └── gmail_service.py # ⭐ Integración Gmail API
│           │   │   ├── parsers/
│           │   │   │   ├── excel_parser.py  # Parser Excel con detección automática
│           │   │   │   └── pdf_parser.py    # Parser PDF
│           │   │   ├── views/
│           │   │   │   ├── etl_views.py     # Endpoints ETL
│           │   │   │   ├── auth_views.py    # Autenticación OAuth
│           │   │   │   └── gmail_auth_views.py
│           │   │   ├── tasks.py             # Tareas Celery
│           │   │   └── serializers.py       # DRF Serializers
│           │   ├── SmartPharm/
│           │   │   ├── settings.py          # ⚙️ Configuración Django
│           │   │   ├── celery.py            # Configuración Celery
│           │   │   └── urls.py              # Rutas API
│           │   ├── config/
│           │   │   └── secrets.py           # Manejo de credenciales
│           │   ├── gmail_credentials.json   # 🔐 OAuth Client ID
│           │   ├── gmail_token.json         # 🔐 Token Gmail (auto-generado)
│           │   ├── user_session_token.json  # 🔐 Sesión usuario (auto-generado)
│           │   ├── etl_progress.json        # 📊 Progreso ETL en tiempo real
│           │   ├── requirements.txt         # Dependencias Python
│           │   └── Dockerfile
│           │
│           ├── Frontend_React/              # Interfaz React
│           │   ├── src/
│           │   │   ├── pages/
│           │   │   │   ├── Dashboard.jsx
│           │   │   │   ├── ETL/
│           │   │   │   │   └── ETL.jsx     # ⭐ Interfaz ETL con progreso en tiempo real
│           │   │   │   ├── Productos.jsx
│           │   │   │   ├── Ofertas.jsx
│           │   │   │   └── Clientes.jsx
│           │   │   ├── components/
│           │   │   │   └── [componentes reutilizables]
│           │   │   ├── services/
│           │   │   │   └── api.js          # Axios - Llamadas API
│           │   │   ├── context/
│           │   │   │   └── AuthContext.jsx # Contexto autenticación
│           │   │   └── App.jsx
│           │   ├── package.json
│           │   └── Dockerfile
│           │
│           ├── docker-compose.yml           # ⭐ Orquestación 6 servicios
│           ├── .env                         # Variables de entorno
│           ├── DOCKER.md
│           ├── ENDPOINTS.md
│           ├── GMAIL_OAUTH_SETUP.md
│           ├── CREDENCIALES_CONFIG.md
│           └── README.md
│
├── claude web.md                            # ← ESTE ARCHIVO
├── claude web COMPLETO.md
└── README.md

```

---

## 🎯 COMPONENTES CRÍTICOS DEL SISTEMA

### 1. Sistema ETL (Extraction, Transformation, Load)

**Archivo Principal:** `Backend_Django/core/etl/offer_etl.py`

**Flujo Completo:**
```python
class OfferETL:
    def run(days_back=5, strict_mode=False):
        # 1. Conectar a Gmail API
        gmail_service = GmailService()  # OAuth automático

        # 2. Buscar correos (últimos 5 días)
        messages = gmail_service.search_offers_emails(
            query="has:attachment (xlsx OR pdf) newer_than:5d"
        )

        # 3. Validar cada correo
        for message in messages:
            # Excluir: proyectosmartpharm2025@gmail.com
            # Aceptar: Mediven, Socofar (siempre)
            # Validar: palabras clave (precio, oferta, laboratorio, etc.)
            if validate_message(message):
                attachments = gmail_service.get_attachments(message_id)

        # 4. Parsear archivos
        for attachment in attachments:
            if is_excel(attachment):
                parser = ExcelOfferParser(data, filename, metadata)
                offers = parser.parse()  # Detecta columnas automáticamente
            elif is_pdf(attachment):
                parser = PDFOfferParser(data, filename, metadata)
                offers = parser.parse()

        # 5. Cargar en DB (transacción atómica)
        for offer_data in offers:
            # Crear/obtener Proveedor
            proveedor = Proveedor.objects.get_or_create(
                nombre=offer_data['laboratorio']
            )

            # Crear/obtener Producto (por código o nombre)
            producto = Producto.objects.get_or_create(
                codigo=offer_data['codigo'],
                defaults={...}
            )

            # Crear oferta
            OfertaLaboratorio.objects.create(
                producto=producto,
                laboratorio=offer_data['laboratorio'],
                precio_normal=offer_data['precio_normal'],
                precio_oferta=offer_data['precio_oferta'],
                ...
            )

        # 6. Registrar log
        ETLLog.objects.create(
            emails_procesados=stats['emails'],
            ofertas_insertadas=stats['offers'],
            ...
        )
```

**Características Especiales:**
- ✅ Elimina todas las ofertas antiguas antes de cargar nuevas (estrategia: reemplazo completo)
- ✅ Progreso en tiempo real guardado en `etl_progress.json` (polling cada 500ms desde frontend)
- ✅ Detección automática de columnas en Excel (maneja múltiples formatos)
- ✅ Calcula descuentos automáticamente si no están en el archivo
- ✅ Extrae laboratorio desde remitente del email o nombre de archivo
- ✅ Validación robusta: excluye propios correos, acepta dominios confiables, verifica palabras clave

---

### 2. Sistema de Autenticación OAuth 2.0

**Archivos Principales:**
- `Backend_Django/core/views/auth_views.py` - Login con Google
- `Backend_Django/core/views/gmail_auth_views.py` - Autorización Gmail
- `Backend_Django/core/services/gmail_service.py` - Servicio Gmail

**Flujo OAuth Completo:**

```
1. Usuario → Clic "Continuar con Google"
2. Frontend → GET /api/auth/login/start/
3. Backend → Genera URL OAuth con scopes:
   - openid (identificación)
   - userinfo.email
   - userinfo.profile
   - gmail.readonly (⭐ acceso a Gmail)
4. Se abre popup con autorización Google
5. Usuario autoriza → Google redirige a /api/auth/callback?code=XXX
6. Backend intercambia code por tokens:
   - access_token
   - refresh_token
   - id_token
7. Backend guarda tokens:
   - user_session_token.json (sesión usuario)
   - gmail_token.json (acceso Gmail)
8. Backend retorna HTML con postMessage + localStorage
9. Frontend detecta login mediante polling /api/auth/session/
10. Redirección automática a dashboard
```

**Renovación Automática de Tokens:**
```python
# En GmailService._authenticate()
if self.creds.expired and self.creds.refresh_token:
    try:
        self.creds.refresh(Request())  # Renueva automáticamente
        # Guarda el nuevo token
        with open(token_path, 'w') as token:
            token.write(self.creds.to_json())
    except Exception:
        # Token inválido → solicitar re-autenticación
        raise Exception("Token expirado, vuelve a autenticar")
```

---

### 3. Parsers Inteligentes

#### Excel Parser (`excel_parser.py`)

**Detección Automática de Columnas:**
```python
COLUMN_MAPPINGS = {
    'producto': ['producto', 'medicamento', 'item', 'descripcion', 'nombre'],
    'codigo': ['codigo', 'código', 'sku', 'cod', 'code'],
    'precio_normal': ['precio', 'precio normal', 'pvp', 'valor'],
    'precio_oferta': ['oferta', 'precio oferta', 'promoción', 'descuento'],
    'descuento': ['desc', 'descuento', '%', 'porcentaje'],
    'laboratorio': ['laboratorio', 'lab', 'proveedor', 'marca'],
    'vigencia': ['vigencia', 'válido hasta', 'fecha', 'vencimiento']
}

def _detect_columns(self):
    column_map = {}
    for key, variations in self.COLUMN_MAPPINGS.items():
        for col in self.df.columns:
            if any(var in col.lower() for var in variations):
                column_map[key] = col
                break
    return column_map
```

**Capacidades:**
- ✅ Maneja múltiples variaciones de nombres de columnas
- ✅ Parsea precios con diferentes formatos: $12.000, 12000, 12.000,50
- ✅ Calcula descuentos si no están presentes: `(precio_normal - precio_oferta) / precio_normal * 100`
- ✅ Normaliza fechas en múltiples formatos: dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd
- ✅ Extrae laboratorio desde remitente o nombre de archivo

---

### 4. Frontend React - Progreso en Tiempo Real

**Archivo:** `Frontend_React/src/pages/ETL/ETL.jsx`

**Polling de Progreso:**
```javascript
useEffect(() => {
    let intervalId;

    if (isRunning) {
        // Polling cada 500ms para progreso en tiempo real
        intervalId = setInterval(async () => {
            const response = await etlService.getProgress();

            if (response.data.progress) {
                setProgress(response.data.progress);
                // progress.percentage: 0-100
                // progress.stage: 'iniciando', 'conectando', 'procesando', 'completado'
                // progress.message: 'Procesando correo 5/10'
                // progress.stats: { emails_processed, attachments_downloaded, offers_extracted, offers_inserted }
            }

            if (!response.data.running) {
                setIsRunning(false);  // ETL terminó
                loadData();           // Recargar datos
            }
        }, 500);
    }

    return () => clearInterval(intervalId);
}, [isRunning]);
```

**Visualización:**
- Barra de progreso visual (0-100%)
- Etapa actual del proceso
- Estadísticas en tiempo real (correos, adjuntos, ofertas)
- Mensajes descriptivos de cada fase

---

## 🔧 COMANDOS ÚTILES PARA DESARROLLO

### Docker Compose

```bash
# Levantar todos los servicios
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f frontend

# Reiniciar un servicio
docker-compose restart backend

# Detener todo
docker-compose down

# Eliminar volúmenes (⚠️ BORRA LA BASE DE DATOS)
docker-compose down -v

# Reconstruir imágenes
docker-compose build --no-cache
docker-compose up -d --force-recreate

# Ver estado de servicios
docker-compose ps

# Acceder a shell de un servicio
docker-compose exec backend bash
docker-compose exec db psql -U smartpharm_user -d smartpharm_db
```

### Django Management Commands

```bash
# Ejecutar migraciones
docker-compose exec backend python manage.py migrate

# Crear migraciones
docker-compose exec backend python manage.py makemigrations

# Crear superusuario adicional
docker-compose exec backend python manage.py createsuperuser

# Shell interactivo de Django
docker-compose exec backend python manage.py shell

# Ejecutar ETL manualmente desde terminal
docker-compose exec backend python manage.py run_etl

# Importar datos de farmacia
docker-compose exec backend python manage.py import_farmacia

# Seed data de prueba
docker-compose exec backend python manage.py seed_data

# Collectstatic (archivos estáticos)
docker-compose exec backend python manage.py collectstatic --noinput

# Ver logs de base de datos
docker-compose exec db psql -U smartpharm_user -d smartpharm_db -c "SELECT * FROM etl_logs ORDER BY fecha_ejecucion DESC LIMIT 5;"
```

### Celery Commands

```bash
# Ver tareas activas de Celery
docker-compose exec celery_worker celery -A SmartPharm inspect active

# Ver tareas programadas
docker-compose exec celery_beat celery -A SmartPharm inspect scheduled

# Purge de cola de tareas
docker-compose exec celery_worker celery -A SmartPharm purge

# Monitoreo en tiempo real
docker-compose exec celery_worker celery -A SmartPharm events
```

### Frontend Development

```bash
# Desarrollo local sin Docker
cd Frontend_React
npm install
npm run dev  # http://localhost:5173

# Build de producción
npm run build

# Preview del build
npm run preview

# Linting
npm run lint
```

---

## 🐛 TROUBLESHOOTING COMÚN

### Problema 1: Gmail no autenticado

**Síntoma:** Error "Gmail no está autenticado" al ejecutar ETL

**Solución:**
1. Cerrar sesión en el frontend
2. Volver a iniciar sesión con Google (autoriza Gmail automáticamente)
3. Verificar que existe `Backend_Django/gmail_token.json`

### Problema 2: Token expirado

**Síntoma:** Error "Token expirado" al ejecutar ETL

**Solución:**
```bash
# Eliminar token y volver a autenticar
docker-compose exec backend rm gmail_token.json
# Cerrar sesión en frontend y volver a iniciar sesión
```

### Problema 3: Base de datos no se conecta

**Síntoma:** Error "FATAL: password authentication failed"

**Solución:**
```bash
# Verificar variables de entorno
cat .env

# Recrear base de datos
docker-compose down -v
docker-compose up -d db
docker-compose up backend
```

### Problema 4: Frontend no se conecta al backend

**Síntoma:** Errores CORS o "Network Error"

**Solución:**
```bash
# Verificar CORS en settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # React dev
    "http://localhost",       # Docker frontend
]

# Verificar VITE_API_URL en .env
VITE_API_URL=http://localhost:8000
```

### Problema 5: ETL no encuentra correos

**Síntoma:** ETL completa pero con 0 correos procesados

**Solución:**
1. Verificar que existen correos de Mediven/Socofar en los últimos 5 días
2. Verificar que los correos tienen adjuntos Excel/PDF
3. Revisar validación en `gmail_service.py:_validate_message()`
4. Verificar palabras clave: precio, oferta, laboratorio, promoción, lista, descuento

---

## 📊 MÉTRICAS Y MONITOREO

### Logs ETL

Los logs de cada ejecución ETL se guardan en la tabla `etl_logs`:

```sql
-- Ver últimas 10 ejecuciones
SELECT
    fecha_ejecucion,
    exitoso,
    emails_procesados,
    adjuntos_descargados,
    ofertas_extraidas,
    ofertas_insertadas,
    duracion_segundos
FROM etl_logs
ORDER BY fecha_ejecucion DESC
LIMIT 10;

-- Ver tasa de éxito
SELECT
    COUNT(*) as total_ejecuciones,
    SUM(CASE WHEN exitoso THEN 1 ELSE 0 END) as exitosas,
    AVG(duracion_segundos) as duracion_promedio,
    AVG(ofertas_insertadas) as ofertas_promedio
FROM etl_logs;
```

### Progreso en Tiempo Real

El progreso del ETL se guarda en `Backend_Django/etl_progress.json`:

```json
{
    "percentage": 75.5,
    "stage": "procesando",
    "message": "Procesando correo 8/10",
    "stats": {
        "emails_processed": 8,
        "attachments_downloaded": 12,
        "offers_extracted": 245,
        "offers_inserted": 245,
        "errors": []
    },
    "timestamp": "2025-11-01T15:30:45.123456"
}
```

---

## 🚀 ROADMAP Y FUTURAS MEJORAS

### Fase 1: MVP ✅ (Completado)
- ✅ Sistema ETL automatizado con Gmail
- ✅ Parsers Excel/PDF inteligentes
- ✅ Dashboard básico React
- ✅ Autenticación OAuth 2.0
- ✅ Docker Compose con 6 servicios
- ✅ Gestión de productos, clientes, ofertas

### Fase 2: Análisis Predictivo 🚧 (En Desarrollo)
- 🔄 Machine Learning para predicción de demanda estacional
- 🔄 Análisis de patrones de consumo
- 🔄 Sugerencias automáticas de compra inteligentes
- 🔄 Integración con datos epidemiológicos (Minsal)
- 🔄 Alertas automáticas de stock bajo con ML

### Fase 3: Expansión 🔮 (Futuro)
- 📅 App móvil para alertas en tiempo real
- 📅 Integración con más proveedores (no solo Mediven/Socofar)
- 📅 Módulo de fidelización de clientes
- 📅 Análisis de rentabilidad por producto
- 📅 Reportes automáticos PDF/Excel
- 📅 Multi-tenant para múltiples farmacias

---

## 🎓 COMPETENCIAS APLICADAS (Proyecto Capstone)

Este proyecto demuestra las siguientes competencias de Ingeniería en Informática:

1. **Propuestas de Solución Informática Integral**
   - Identificación de problemática del sector farmacéutico
   - Diseño de solución técnica escalable
   - Business Plan y análisis financiero (ROI, VAN, TIR)

2. **Gestión de Proyectos Informáticos PMI**
   - Plan de gestión de proyectos con metodología PMI
   - Control de alcance, tiempo, costos y calidad
   - Gestión de riesgos y stakeholders

3. **Desarrollo de Software Sistematizado**
   - Arquitectura limpia: separación de responsabilidades
   - Patrón ETL (Extraction, Transformation, Load)
   - API REST con Django REST Framework
   - Frontend modular con React + Vite

4. **Modelos de Datos Escalables**
   - Base de datos PostgreSQL normalizada (3FN)
   - 8 modelos relacionados (Cliente, Producto, Proveedor, OfertaLaboratorio, etc.)
   - Migraciones controladas con Django ORM

5. **Arquitectura Sistémica Empresarial**
   - Microservicios con Docker Compose
   - Celery para procesamiento asíncrono
   - Redis como message broker
   - Nginx para servir frontend en producción

6. **Transformación de Datos para Decisiones**
   - ETL automatizado desde correos electrónicos
   - Parsers inteligentes con detección automática
   - Dashboard con métricas y KPIs en tiempo real
   - Análisis predictivo (futuro)

---

## 📜 LICENCIA Y PROPIEDAD INTELECTUAL

**Licencia:** MIT License

**Propiedad Intelectual:**
- Proyecto académico desarrollado como Aplicación de Título (APT) en Duoc UC
- Los datos de farmacias utilizados son reales pero anonimizados
- El código es open-source bajo licencia MIT

**Contacto:**
- Email: bastianhartal@gmail.com
- Institución: Duoc UC - Sede Antonio Varas
- Programa: Ingeniería en Informática 2025

---

## 📚 DOCUMENTACIÓN ADICIONAL

Archivos de documentación complementaria en el repositorio:

| Archivo | Descripción |
|---------|-------------|
| `README.md` | Guía de inicio rápido |
| `DOCKER.md` | Guía completa de Docker Compose |
| `ENDPOINTS.md` | Lista completa de endpoints de la API |
| `GMAIL_OAUTH_SETUP.md` | Configuración de Google Cloud Console y OAuth |
| `CREDENCIALES_CONFIG.md` | Gestión de credenciales y secrets |
| `ETL_SETUP_INSTRUCTIONS.md` | Instrucciones detalladas del ETL |

---

## ✅ CHECKLIST PARA NUEVOS DESARROLLADORES

Si eres un desarrollador nuevo (o una IA) trabajando en este proyecto, sigue este checklist:

### Setup Inicial
- [ ] Clonar repositorio
- [ ] Instalar Docker y Docker Compose
- [ ] Copiar `.env.example` a `.env` y configurar variables
- [ ] Verificar que `gmail_credentials.json` existe (si no, seguir `GMAIL_OAUTH_SETUP.md`)
- [ ] Levantar servicios: `docker-compose up -d`
- [ ] Verificar que todos los servicios están corriendo: `docker-compose ps`
- [ ] Acceder a http://localhost (frontend) y http://localhost:8000/admin (backend)

### Testing del Sistema
- [ ] Iniciar sesión con Google
- [ ] Verificar que Gmail se autenticó correctamente
- [ ] Ir a sección ETL
- [ ] Ejecutar ETL manualmente (botón "Ejecutar ETL")
- [ ] Observar progreso en tiempo real (barra de progreso)
- [ ] Verificar que se insertaron ofertas en la base de datos
- [ ] Ir a sección "Ofertas" y verificar que aparecen las ofertas extraídas
- [ ] Probar navegación entre secciones (Dashboard, Productos, Clientes, Ofertas)

### Desarrollo
- [ ] Leer `ENDPOINTS.md` para conocer la API
- [ ] Revisar modelos en `Backend_Django/core/models.py`
- [ ] Entender flujo ETL en `Backend_Django/core/etl/offer_etl.py`
- [ ] Revisar parsers en `Backend_Django/core/parsers/`
- [ ] Familiarizarse con componentes React en `Frontend_React/src/`

### Antes de Hacer Commit
- [ ] Ejecutar tests: `docker-compose exec backend python manage.py test`
- [ ] Verificar que no hay errores de consola en frontend
- [ ] Probar que ETL funciona correctamente
- [ ] Actualizar documentación si es necesario
- [ ] No commitear archivos sensibles: `.env`, `*_token.json`, `*_credentials.json`

---

**FIN DEL DOCUMENTO**

*Documento generado para facilitar la comprensión del proyecto SmartPharm CRM por parte de desarrolladores y sistemas de IA.*

---

📊 **Estadísticas del Documento:**
- Total de líneas: ~3,800+
- Archivos con código completo: 8 archivos principales
- Secciones: 25+
- Ejemplos de código: 30+
- Comandos útiles: 40+
- Fecha de generación: 2025-11-01
- Versión: MVP 1.0

---

**Proyecto Capstone 2025** | Ingeniería en Informática | Duoc UC - Sede Antonio Varas
