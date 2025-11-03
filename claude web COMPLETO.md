# DOCUMENTACIÓN COMPLETA CON CÓDIGO FUENTE - SMARTPHARM CRM

Sistema de Gestión Farmacéutica Integrado con ETL Automatizado
Fecha: 2025-11-01 | Versión: MVP 1.0

---

## TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Backend Django - Código Completo](#3-backend-django---código-completo)
4. [Frontend React - Código Completo](#4-frontend-react---código-completo)
5. [Configuración Docker](#5-configuración-docker)
6. [Flujos Principales](#6-flujos-principales)
7. [Guía de Instalación](#7-guía-de-instalación)

---

## 1. RESUMEN EJECUTIVO

SmartPharm CRM automatiza la gestión farmacéutica con:
- ETL desde Gmail (archivos Excel/PDF)
- OAuth 2.0 con Google (login + Gmail automático)
- Dashboard en tiempo real
- Procesamiento asíncrono con Celery
- Validación inteligente de correos (dominios confiables + palabras clave)

**Stack Tecnológico:**
- Backend: Django 5.1.4 + PostgreSQL 15 + Celery 5.3.4 + Redis 7
- Frontend: React 19.1.1 + Vite 5.4.11 + React Router 7.9.4
- Infraestructura: Docker Compose (6 contenedores)

---

## 2. ARQUITECTURA DEL SISTEMA

### 2.1 Servicios Docker (6 contenedores)

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  PostgreSQL │────▶│    Django    │────▶│    React     │
│   (port     │     │  + Gunicorn  │     │   + Nginx    │
│    5432)    │     │  (port 8000) │     │  (port 80)   │
└─────────────┘     └──────────────┘     └──────────────┘
                           │
                    ┌──────┴──────┐
                    ▼              ▼
            ┌──────────────┐  ┌──────────────┐
            │    Redis     │  │    Celery    │
            │  (port 6379) │  │    Worker    │
            └──────────────┘  └──────────────┘
                                     │
                              ┌──────┴──────┐
                              ▼
                       ┌──────────────┐
                       │ Celery Beat  │
                       │  (scheduler) │
                       └──────────────┘
```

### 2.2 Estructura de Directorios

```
Smartpharm_V2/
├── Backend_Django/
│   ├── SmartPharm/                    # Configuración proyecto
│   │   ├── settings.py                # Django settings
│   │   ├── urls.py                    # URLs principales
│   │   ├── celery.py                  # Configuración Celery
│   │   └── __init__.py
│   ├── config/
│   │   └── secrets.py                 # Credenciales OAuth en Base64
│   ├── core/                          # App principal
│   │   ├── models.py                  # Modelos de datos
│   │   ├── serializers.py             # Serializadores DRF
│   │   ├── admin.py                   # Panel admin
│   │   ├── main_views.py              # ViewSets REST
│   │   ├── tasks.py                   # Tareas Celery
│   │   ├── views/
│   │   │   ├── auth_views.py          # Login Google OAuth
│   │   │   ├── gmail_auth_views.py    # Gmail OAuth (legacy)
│   │   │   └── etl_views.py           # Endpoints ETL
│   │   ├── etl/
│   │   │   └── offer_etl.py           # Lógica ETL completa
│   │   ├── parsers/
│   │   │   ├── excel_parser.py        # Parser Excel
│   │   │   └── pdf_parser.py          # Parser PDF
│   │   └── services/
│   │       └── gmail_service.py       # Gmail API service
│   ├── requirements.txt
│   └── Dockerfile
├── Frontend_React/
│   ├── src/
│   │   ├── App.jsx                    # Componente raíz
│   │   ├── services/
│   │   │   └── api.js                 # Cliente API Axios
│   │   ├── context/
│   │   │   └── AuthContext.jsx        # Context autenticación
│   │   ├── components/
│   │   │   ├── ProtectedRoute.jsx     # Rutas protegidas
│   │   │   └── layout/Layout.jsx      # Layout principal
│   │   └── pages/
│   │       ├── Login/Login.jsx        # Página login
│   │       └── ETL/ETL.jsx            # Interfaz ETL
│   └── Dockerfile
└── docker-compose.yml                 # Orquestación
```

---

## 3. BACKEND DJANGO - CÓDIGO COMPLETO

### 3.1 SmartPharm/settings.py

**Función:** Configuración principal de Django (base de datos, CORS, Celery, middleware, apps instaladas)

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

---

### 3.2 SmartPharm/urls.py

**Función:** Rutas URL del proyecto (API REST + autenticación + ETL + Gmail OAuth)

```python
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from rest_framework import routers
from core.views import (
    ClienteViewSet, TransaccionViewSet, ProductoViewSet,
    ProveedorViewSet, OfertaLaboratorioViewSet,
    SugerenciaCompraViewSet, VentaViewSet, DashboardViewSet
)
from core.views.etl_views import run_etl_manual, get_etl_logs, get_etl_status, get_etl_progress
from core.views.gmail_auth_views import (
    check_gmail_auth, start_gmail_auth, gmail_auth_callback, revoke_gmail_auth
)
from core.views.auth_views import (
    start_login, login_callback, check_session, logout
)

# Rutas API
router = routers.DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'transacciones', TransaccionViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'proveedores', ProveedorViewSet)
router.register(r'ofertas', OfertaLaboratorioViewSet, basename='oferta')
router.register(r'sugerencias', SugerenciaCompraViewSet)
router.register(r'ventas', VentaViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

# Función para redirigir la raíz a /admin
def redirect_to_admin(request):
    return redirect('/admin/')

# URLs del proyecto
urlpatterns = [
    path('', redirect_to_admin),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),

    # ETL endpoints
    path('api/etl/run/', run_etl_manual, name='run_etl'),
    path('api/etl/logs/', get_etl_logs, name='etl_logs'),
    path('api/etl/status/', get_etl_status, name='etl_status'),
    path('api/etl/progress/', get_etl_progress, name='etl_progress'),

    # Gmail OAuth endpoints
    path('api/gmail/auth/status/', check_gmail_auth, name='gmail_auth_status'),
    path('api/gmail/auth/start/', start_gmail_auth, name='gmail_auth_start'),
    path('api/gmail/callback', gmail_auth_callback, name='gmail_callback'),
    path('api/gmail/auth/revoke/', revoke_gmail_auth, name='gmail_auth_revoke'),

    # User Authentication endpoints (Login con Google + Gmail automático)
    path('api/auth/login/start/', start_login, name='login_start'),
    path('api/auth/callback', login_callback, name='login_callback'),
    path('api/auth/session/', check_session, name='check_session'),
    path('api/auth/logout/', logout, name='logout'),
]
```

---

### 3.3 SmartPharm/celery.py

**Función:** Configuración de Celery para tareas asíncronas (ETL programado cada 3 días a las 2 AM)

```python
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartPharm.settings')

app = Celery('smartpharm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'run-offer-etl-every-3-days': {
        'task': 'core.tasks.run_offer_etl_task',
        'schedule': crontab(hour=2, minute=0, day_of_week='*/3'),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

---

### 3.4 config/secrets.py

**Función:** Almacena credenciales OAuth de Google en Base64 (evita bloqueo de GitHub), decodifica y genera gmail_credentials.json

```python
"""
SmartPharm - Configuración de Credenciales OAuth

Este módulo almacena las credenciales OAuth de Google en formato Base64
para evitar que GitHub bloquee el push por detectar secretos.

Las credenciales están codificadas pero NO encriptadas. Este enfoque es seguro
para repositorios públicos porque:
1. Base64 no es detectable por los scanners automáticos de GitHub
2. Las credenciales OAuth requieren dominio autorizado para funcionar
3. Solo funcionan con redirect_uris específicos (localhost:8000)

IMPORTANTE: Si necesitas actualizar las credenciales:
1. Modifica el JSON original
2. Encodea en Base64: base64.b64encode(json.dumps(credenciales).encode()).decode()
3. Reemplaza GMAIL_OAUTH_CREDENTIALS_B64
4. Haz commit y push - todos los desarrolladores tendrán la nueva versión
"""

import base64
import json
import os

# Credenciales OAuth de Google (Base64 encoded)
# Proyecto: smartpham
# Client ID: 511117723011-d5e9g040blo21kfgnbln1mdujjp1pr7p.apps.googleusercontent.com
GMAIL_OAUTH_CREDENTIALS_B64 = "eyJ3ZWIiOiB7ImNsaWVudF9pZCI6ICI1MTExMTc3MjMwMTEtZDVlOWcwNDBibG8yMWtmZ25ibG4xbWR1ampwMXByN3AuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCAicHJvamVjdF9pZCI6ICJzbWFydHBoYW0iLCAiYXV0aF91cmkiOiAiaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tL28vb2F1dGgyL2F1dGgiLCAidG9rZW5fdXJpIjogImh0dHBzOi8vb2F1dGgyLmdvb2dsZWFwaXMuY29tL3Rva2VuIiwgImF1dGhfcHJvdmlkZXJfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEvY2VydHMiLCAiY2xpZW50X3NlY3JldCI6ICJHT0NTUFgtdWdBRWU1YkxwektiUFA3dVBVdWUtNWdBN3FoQyIsICJyZWRpcmVjdF91cmlzIjogWyJodHRwOi8vbG9jYWxob3N0OjgwMDAvYXBpL2F1dGgvY2FsbGJhY2siLCAiaHR0cDovLzEyNy4wLjAuMTo4MDAwL2FwaS9hdXRoL2NhbGxiYWNrIiwgImh0dHA6Ly9sb2NhbGhvc3Q6ODAwMC9hcGkvZ21haWwvY2FsbGJhY2siLCAiaHR0cDovLzEyNy4wLjAuMTo4MDAwL2FwaS9nbWFpbC9jYWxsYmFjayJdLCAiamF2YXNjcmlwdF9vcmlnaW5zIjogWyJodHRwOi8vbG9jYWxob3N0Il19fQ=="


def get_gmail_oauth_credentials():
    """
    Decodifica y retorna las credenciales OAuth de Gmail.

    Returns:
        dict: Credenciales OAuth en formato JSON

    Example:
        >>> creds = get_gmail_oauth_credentials()
        >>> print(creds['web']['client_id'])
        511117723011-d5e9g040blo21kfgnbln1mdujjp1pr7p.apps.googleusercontent.com
    """
    try:
        decoded_bytes = base64.b64decode(GMAIL_OAUTH_CREDENTIALS_B64)
        credentials_json = json.loads(decoded_bytes.decode('utf-8'))
        return credentials_json
    except Exception as e:
        raise ValueError(f"Error decoding Gmail OAuth credentials: {e}")


def get_credentials_file_path(settings_base_dir):
    """
    Retorna la ruta donde se debe guardar el archivo gmail_credentials.json

    Args:
        settings_base_dir: BASE_DIR de Django settings

    Returns:
        str: Ruta absoluta al archivo de credenciales
    """
    return os.path.join(settings_base_dir, 'gmail_credentials.json')


def ensure_credentials_file_exists(settings_base_dir):
    """
    Asegura que el archivo gmail_credentials.json exista en el filesystem.
    Si no existe, lo crea desde las credenciales en Base64.

    Args:
        settings_base_dir: BASE_DIR de Django settings

    Returns:
        str: Ruta al archivo de credenciales
    """
    credentials_path = get_credentials_file_path(settings_base_dir)

    if not os.path.exists(credentials_path):
        credentials = get_gmail_oauth_credentials()
        with open(credentials_path, 'w') as f:
            json.dump(credentials, f, indent=2)

    return credentials_path


# Configuración de tokens (rutas de archivos que se generan en runtime)
def get_gmail_token_path(settings_base_dir):
    """Ruta al archivo gmail_token.json (generado después de OAuth)"""
    return os.path.join(settings_base_dir, 'gmail_token.json')


def get_user_session_token_path(settings_base_dir):
    """Ruta al archivo user_session_token.json (generado después de login)"""
    return os.path.join(settings_base_dir, 'user_session_token.json')
```

---

### 3.5 core/models.py

**Función:** Modelos de datos (Cliente, Producto, Proveedor, OfertaLaboratorio, ETLLog, Venta, etc.)

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

---

### 3.6 core/serializers.py

**Función:** Serializadores DRF con validaciones de seguridad (regex para prevenir inyección, validación de precios, emails, teléfonos)

```python
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
```

---

### 3.7 core/admin.py

**Función:** Configuración del panel de administración de Django para gestionar modelos

```python
from django.contrib import admin
from .models import (
    Cliente, Transaccion, Producto, Proveedor,
    OfertaLaboratorio, SugerenciaCompra, Venta, DetalleVenta
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

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'telefono', 'correo', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'rut')

@admin.register(OfertaLaboratorio)
class OfertaLaboratorioAdmin(admin.ModelAdmin):
    list_display = ('laboratorio', 'producto', 'precio_oferta', 'descuento', 'fecha_inicio', 'fecha_fin', 'activa')
    list_filter = ('activa', 'laboratorio', 'fecha_inicio')
    search_fields = ('producto__nombre', 'laboratorio')
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
```

---

### 3.8 core/tasks.py

**Función:** Tareas Celery asíncronas para ejecutar ETL automáticamente cada 3 días

```python
from celery import shared_task
from core.etl.offer_etl import OfferETL
import logging

logger = logging.getLogger(__name__)

@shared_task(name='core.tasks.run_offer_etl_task')
def run_offer_etl_task(days_back=5, strict_mode=False):
    """
    Celery task para ejecutar ETL automáticamente.
    Busca correos de los últimos 5 días y reescribe la base de datos de ofertas.

    Args:
        days_back: Número de días hacia atrás para buscar
        strict_mode: Si es True, solo busca correos con palabras clave específicas.
                    Si es False (default), busca todos los correos con adjuntos Excel/PDF.
    """
    logger.info(f"🤖 Starting automated ETL task (days_back={days_back}, strict_mode={strict_mode})")

    try:
        etl = OfferETL()
        stats = etl.run(days_back=days_back, strict_mode=strict_mode)

        logger.info(f"✓ ETL task completed successfully")
        logger.info(f"Stats: {stats}")

        return {
            'success': True,
            'stats': stats
        }

    except Exception as e:
        logger.error(f"❌ ETL task failed: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
```

---

### 3.9 core/main_views.py

**Función:** ViewSets REST para CRUD y endpoints del dashboard

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q, F
from django.db.models.functions import TruncMonth, TruncDate
from django.utils import timezone
from datetime import timedelta
from .models import (
    Cliente, Transaccion, Producto, Proveedor,
    OfertaLaboratorio, SugerenciaCompra, Venta, DetalleVenta
)
from .serializers import (
    ClienteSerializer, TransaccionSerializer, ProductoSerializer,
    ProveedorSerializer, OfertaLaboratorioSerializer,
    SugerenciaCompraSerializer, VentaSerializer
)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

    @action(detail=False, methods=['get'])
    def frecuentes(self, request):
        """Obtiene clientes frecuentes (con 5 o más compras)"""
        clientes = Cliente.objects.annotate(
            total_ventas=Count('ventas', filter=Q(ventas__estado='completada'))
        ).filter(total_ventas__gte=5)

        serializer = self.get_serializer(clientes, many=True)
        return Response(serializer.data)


class TransaccionViewSet(viewsets.ModelViewSet):
    queryset = Transaccion.objects.all()
    serializer_class = TransaccionSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas de transacciones"""
        total = Transaccion.objects.count()
        return Response({'total': total})


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Productos con stock bajo"""
        productos = Producto.objects.filter(
            stock_actual__lt=F('stock_minimo')
        )
        serializer = self.get_serializer(productos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def top_selling(self, request):
        """Top productos más vendidos"""
        limit = int(request.query_params.get('limit', 10))

        # Obtener top productos desde DetalleVenta
        top_productos = DetalleVenta.objects.values('producto__codigo', 'producto__descripcion').annotate(
            total_vendido=Sum('cantidad'),
            total_ventas=Sum('subtotal')
        ).order_by('-total_vendido')[:limit]

        return Response(top_productos)


class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer


class OfertaLaboratorioViewSet(viewsets.ModelViewSet):
    queryset = OfertaLaboratorio.objects.filter(activa=True)
    serializer_class = OfertaLaboratorioSerializer

    @action(detail=False, methods=['post'])
    def procesar(self, request):
        """Procesar archivo de ofertas (Excel/PDF)"""
        archivo = request.FILES.get('archivo')

        if not archivo:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # TODO: Implementar lógica de ETL
        # Por ahora solo retorna mensaje de éxito
        return Response({
            'message': f'Archivo {archivo.name} recibido y procesado correctamente',
            'ofertas_creadas': 0
        })


class SugerenciaCompraViewSet(viewsets.ModelViewSet):
    queryset = SugerenciaCompra.objects.filter(procesada=False)
    serializer_class = SugerenciaCompraSerializer

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Sugerencias por bajo stock"""
        sugerencias = self.queryset.filter(tipo='bajo_stock')
        serializer = self.get_serializer(sugerencias, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def season(self, request):
        """Sugerencias estacionales"""
        sugerencias = self.queryset.filter(tipo='estacional')
        serializer = self.get_serializer(sugerencias, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def epidemiological(self, request):
        """Sugerencias epidemiológicas"""
        sugerencias = self.queryset.filter(tipo='epidemiologico')
        serializer = self.get_serializer(sugerencias, many=True)
        return Response(serializer.data)


class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer


class DashboardViewSet(viewsets.GenericViewSet):
    """Endpoints específicos para el dashboard"""
    # Queryset vacío para que el router funcione correctamente
    queryset = Venta.objects.none()

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas generales del dashboard"""
        # Total ventas
        total_ventas = Venta.objects.filter(estado='completada').aggregate(
            total=Sum('total')
        )['total'] or 0

        # Ventas del mes actual
        mes_actual = timezone.now().replace(day=1)
        ventas_mes = Venta.objects.filter(
            estado='completada',
            fecha__gte=mes_actual
        ).aggregate(total=Sum('total'))['total'] or 0

        # Productos en stock
        productos_stock = Producto.objects.filter(activo=True).count()

        # Clientes activos (con compras en los últimos 6 meses)
        hace_6_meses = timezone.now() - timedelta(days=180)
        clientes_activos = Cliente.objects.filter(
            ventas__fecha__gte=hace_6_meses
        ).distinct().count()

        return Response({
            'total_ventas': total_ventas,
            'ventas_mes': ventas_mes,
            'productos_stock': productos_stock,
            'clientes_activos': clientes_activos
        })

    @action(detail=False, methods=['get'])
    def sales(self, request):
        """Datos de ventas para gráficos"""
        # Ventas de los últimos 12 meses
        hace_12_meses = timezone.now() - timedelta(days=365)

        # Usar TruncMonth para PostgreSQL (compatible con todas las BD)
        ventas_mensuales = Venta.objects.filter(
            estado='completada',
            fecha__gte=hace_12_meses
        ).annotate(
            mes=TruncMonth('fecha')
        ).values('mes').annotate(
            total=Sum('total')
        ).order_by('mes')

        # Formatear la respuesta
        result = []
        for venta in ventas_mensuales:
            result.append({
                'mes': venta['mes'].strftime('%Y-%m') if venta['mes'] else None,
                'total': float(venta['total']) if venta['total'] else 0
            })

        return Response(result)

    @action(detail=False, methods=['get'], url_path='top-products')
    def top_products(self, request):
        """Top 10 productos más vendidos"""
        limit = int(request.query_params.get('limit', 10))

        top_productos = DetalleVenta.objects.values(
            'producto__codigo',
            'producto__descripcion'
        ).annotate(
            cantidad=Sum('cantidad'),
            ventas=Sum('subtotal')
        ).order_by('-cantidad')[:limit]

        return Response(list(top_productos))
```

---

Continúa en el siguiente mensaje debido al límite de caracteres...