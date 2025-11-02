# 🚀 Sistema ETL SmartPharm - Instrucciones de Configuración

## ✅ Implementación Completada

Se ha implementado un sistema ETL completo que incluye:

### Backend (Django)
- ✅ Configuración de Celery con Redis
- ✅ Servicio de integración con Gmail API
- ✅ Parsers para archivos Excel y PDF
- ✅ Modelos actualizados (OfertaLaboratorio, ETLLog, Producto, Proveedor)
- ✅ Proceso ETL completo
- ✅ Tareas automatizadas con Celery Beat
- ✅ Comandos de management
- ✅ API endpoints REST

### Frontend (React)
- ✅ Página ETL con interfaz completa
- ✅ Botón "Ejecutar ETL y Actualizar Precios"
- ✅ Historial de ejecuciones
- ✅ Estadísticas en tiempo real
- ✅ Menú lateral con opción ETL

### Docker
- ✅ Servicios Redis, Celery Worker y Celery Beat configurados

---

## 📋 Pasos para Completar la Configuración

### PASO 1: Configurar Gmail API

Para que el ETL funcione, necesitas configurar la API de Gmail:

#### 1.1. Crear Proyecto en Google Cloud Console
1. Ve a https://console.cloud.google.com/
2. Crea un nuevo proyecto (o selecciona uno existente)
3. Nombre sugerido: "SmartPharm ETL"

#### 1.2. Habilitar Gmail API
1. En el menú lateral, ve a "APIs y servicios" > "Biblioteca"
2. Busca "Gmail API"
3. Haz clic en "Habilitar"

#### 1.3. Crear Credenciales OAuth 2.0
1. Ve a "APIs y servicios" > "Credenciales"
2. Haz clic en "+ CREAR CREDENCIALES" > "ID de cliente de OAuth"
3. Si es la primera vez, configura la pantalla de consentimiento:
   - Tipo: Externo
   - Nombre de la aplicación: SmartPharm ETL
   - Correo electrónico de asistencia: tu email
   - Ámbitos: Solo agrega los básicos
4. Tipo de aplicación: "Aplicación de escritorio"
5. Nombre: "SmartPharm Desktop Client"
6. Haz clic en "Crear"

#### 1.4. Descargar Credenciales
1. Descarga el archivo JSON de credenciales
2. Renómbralo a `gmail_credentials.json`
3. Colócalo en: `Backend_Django/gmail_credentials.json`

### PASO 2: Generar Migraciones y Aplicarlas

```bash
cd "Fase 2/Evidencias_Proyecto/sistema_aplicacion_V2"

# Opción A: Con Docker (recomendado)
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Opción B: Sin Docker (si estás en entorno local)
cd Backend_Django
python manage.py makemigrations
python manage.py migrate
```

### PASO 3: Instalar Dependencias

Las nuevas dependencias ya están en `requirements.txt`. Si los contenedores ya están corriendo:

```bash
# Reconstruir el contenedor backend
docker-compose build backend

# O reinstalar dependencias en el contenedor existente
docker-compose exec backend pip install -r requirements.txt
```

### PASO 4: Iniciar Todos los Servicios

```bash
cd "Fase 2/Evidencias_Proyecto/sistema_aplicacion_V2"

# Detener servicios existentes
docker-compose down

# Iniciar todos los servicios (incluyendo Redis, Celery Worker y Celery Beat)
docker-compose up -d

# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs específicos de Celery
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

### PASO 5: Autenticar Gmail (Primera Vez)

La primera vez que ejecutes el ETL, necesitas autenticarte con Gmail:

```bash
# Conectarte al contenedor backend
docker-compose exec backend bash

# Ejecutar ETL manualmente para autenticar
python manage.py run_etl

# Seguir las instrucciones en pantalla:
# 1. Se abrirá un navegador
# 2. Inicia sesión con tu cuenta de Gmail
# 3. Autoriza la aplicación
# 4. El token se guardará en gmail_token.json
```

**NOTA:** Si estás en Docker y no puedes abrir un navegador, necesitarás:
1. Ejecutar el comando en tu máquina local (fuera de Docker) una vez
2. O configurar port forwarding para la autenticación OAuth

### PASO 6: Verificar que Todo Funciona

#### 6.1. Verificar Servicios Docker
```bash
docker-compose ps

# Deberías ver estos servicios corriendo:
# - smartpharm_db
# - smartpharm_backend
# - smartpharm_redis
# - smartpharm_celery_worker
# - smartpharm_celery_beat
# - smartpharm_frontend
```

#### 6.2. Probar Celery
```bash
# Ver logs del worker
docker-compose logs celery_worker

# Ver logs del beat scheduler
docker-compose logs celery_beat

# Deberías ver mensajes como:
# "celery@... ready"
# "beat: Starting..."
```

#### 6.3. Acceder al Frontend
1. Abre http://localhost (o el puerto configurado)
2. Ve al menú lateral y haz clic en "ETL"
3. Deberías ver la página del sistema ETL

#### 6.4. Ejecutar ETL Manualmente
1. En la página ETL, haz clic en "🚀 Ejecutar ETL y Actualizar Precios"
2. Verás un mensaje de confirmación
3. Espera unos segundos y recarga para ver los resultados
4. Revisa la sección "Historial de Ejecuciones"

---

## 🔧 Comandos Útiles

### Backend - Django Management Commands
```bash
# Ejecutar ETL manualmente desde terminal
docker-compose exec backend python manage.py run_etl

# Ejecutar ETL de los últimos 7 días
docker-compose exec backend python manage.py run_etl --days 7

# Crear superusuario
docker-compose exec backend python manage.py createsuperuser

# Acceder a Django shell
docker-compose exec backend python manage.py shell
```

### Celery - Monitoreo y Debug
```bash
# Ver tareas programadas en Celery Beat
docker-compose exec backend python manage.py shell
>>> from django_celery_beat.models import PeriodicTask
>>> PeriodicTask.objects.all()

# Ejecutar tarea de Celery manualmente (desde Django shell)
>>> from core.tasks import run_offer_etl_task
>>> result = run_offer_etl_task.delay(3)
>>> result.get()

# Reiniciar servicios Celery
docker-compose restart celery_worker celery_beat
```

### Logs y Debugging
```bash
# Ver logs en tiempo real
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat

# Ver logs de ETL específicos
docker-compose exec backend grep -r "ETL" /app/logs/
```

---

## 📊 Estructura del Sistema

### Flujo del ETL

```
┌─────────────────┐
│   Gmail API     │  ← Busca emails con adjuntos de laboratorios
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Celery Worker   │  ← Procesa archivos Excel/PDF
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Parsers       │  ← Extrae ofertas de archivos
│ (Excel/PDF)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PostgreSQL     │  ← Almacena ofertas y productos
│  (Base de Datos)│
└─────────────────┘
```

### Ejecución Automática
- **Celery Beat** ejecuta el ETL cada 3 días a las 2:00 AM
- Configurable en `Backend_Django/SmartPharm/celery.py`

### Ejecución Manual
- Desde el frontend: Botón "Ejecutar ETL"
- Desde terminal: `python manage.py run_etl`
- Desde API: `POST /api/etl/run/`

---

## ⚠️ Problemas Comunes y Soluciones

### 1. "Gmail credentials not found"
**Solución:** Asegúrate de tener `gmail_credentials.json` en `Backend_Django/`

### 2. "Celery worker not running"
**Solución:**
```bash
docker-compose restart celery_worker
docker-compose logs celery_worker
```

### 3. "No hay registros de ETL"
**Solución:** Ejecuta el ETL manualmente una vez:
```bash
docker-compose exec backend python manage.py run_etl
```

### 4. "Error al parsear Excel/PDF"
**Solución:** Verifica que los archivos tengan el formato esperado:
- Excel: Debe tener columnas como "producto", "precio", "oferta"
- PDF: Debe tener tablas o texto con precios

### 5. "Migraciones pendientes"
**Solución:**
```bash
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```

---

## 🎯 Próximos Pasos

1. **Configurar Gmail API** (obligatorio)
2. **Aplicar migraciones** de base de datos
3. **Iniciar servicios Docker** completos
4. **Autenticar Gmail** por primera vez
5. **Probar ETL manual** desde el frontend
6. **Verificar resultados** en la tabla de ofertas

---

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs: `docker-compose logs -f`
2. Verifica que todos los servicios estén corriendo: `docker-compose ps`
3. Consulta la sección "Problemas Comunes" arriba

---

## 🎉 ¡Sistema Listo!

Una vez completados los pasos de configuración, el sistema ETL estará completamente operativo:
- ✅ Descarga automática de ofertas de Gmail
- ✅ Procesamiento de Excel y PDF
- ✅ Actualización automática de precios
- ✅ Interfaz web para monitoreo
- ✅ Ejecución programada cada 3 días

**¡Disfruta de tu sistema ETL automatizado!** 🚀
