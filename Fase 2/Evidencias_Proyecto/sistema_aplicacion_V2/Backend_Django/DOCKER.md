# SmartPharm - Guía de Docker

Esta guía te ayudará a levantar el proyecto SmartPharm completo usando Docker y Docker Compose.

## Requisitos Previos

- **Docker Desktop** instalado (incluye Docker Compose)
  - Windows: https://docs.docker.com/desktop/install/windows-install/
  - Docker versión 20.10+ recomendada

## Arquitectura de Contenedores

El proyecto está compuesto por 3 servicios principales:

1. **PostgreSQL Database** (`db`) - Puerto 5432
2. **Django Backend** (`backend`) - Puerto 8000
3. **React Frontend** (`frontend`) - Puerto 80

## Comandos Principales

### 1. Levantar todos los servicios (Primera vez)

```bash
cd C:\Users\usuario\Desktop\Smartpharm\SmartPharm
docker-compose up --build
```

**Explicación:**
- `--build`: Construye las imágenes desde cero
- Este comando levanta todos los servicios (db, backend, frontend)
- Las migraciones de Django se ejecutan automáticamente

### 2. Levantar servicios (ejecuciones posteriores)

```bash
docker-compose up
```

Si quieres ejecutarlo en segundo plano (modo detached):

```bash
docker-compose up -d
```

### 3. Detener los servicios

```bash
docker-compose down
```

Para detener y **eliminar volúmenes** (borra la base de datos):

```bash
docker-compose down -v
```

### 4. Ver logs de los servicios

Ver todos los logs:
```bash
docker-compose logs -f
```

Ver logs de un servicio específico:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### 5. Reconstruir un servicio específico

```bash
# Reconstruir solo el backend
docker-compose up --build backend

# Reconstruir solo el frontend
docker-compose up --build frontend
```

### 6. Ejecutar comandos dentro de un contenedor

**Crear un superusuario de Django:**
```bash
docker-compose exec backend python manage.py createsuperuser
```

**Ejecutar migraciones manualmente:**
```bash
docker-compose exec backend python manage.py migrate
```

**Ejecutar shell de Django:**
```bash
docker-compose exec backend python manage.py shell
```

**Acceder a la base de datos PostgreSQL:**
```bash
docker-compose exec db psql -U smartpharm_user -d smartpharm_db
```

**Acceder al contenedor con bash:**
```bash
docker-compose exec backend sh
docker-compose exec frontend sh
```

### 7. Ver estado de los contenedores

```bash
docker-compose ps
```

### 8. Reiniciar un servicio

```bash
docker-compose restart backend
docker-compose restart frontend
docker-compose restart db
```

## Acceso a los Servicios

Una vez que los contenedores estén corriendo:

- **Frontend (React)**: http://localhost
- **Backend (Django API)**: http://localhost:8000/api/
- **Django Admin**: http://localhost:8000/admin/
- **PostgreSQL**: localhost:5432

## Comandos de Limpieza

### Detener y eliminar todo

```bash
docker-compose down --rmi all -v
```

**Explicación:**
- `--rmi all`: Elimina todas las imágenes creadas
- `-v`: Elimina los volúmenes (base de datos)

### Limpiar Docker completamente

```bash
# Eliminar contenedores detenidos
docker container prune -f

# Eliminar imágenes sin usar
docker image prune -a -f

# Eliminar volúmenes sin usar
docker volume prune -f

# Eliminar redes sin usar
docker network prune -f

# Limpiar todo (⚠️ CUIDADO: elimina TODOS los recursos de Docker)
docker system prune -a --volumes -f
```

## Flujo de Trabajo Típico

### Desarrollo Diario

```bash
# 1. Iniciar servicios
docker-compose up -d

# 2. Ver logs en tiempo real
docker-compose logs -f

# 3. Al terminar, detener servicios
docker-compose down
```

### Actualizar Dependencias

**Backend (requirements.txt):**
```bash
# 1. Detener servicios
docker-compose down

# 2. Reconstruir backend
docker-compose build backend

# 3. Levantar servicios
docker-compose up -d
```

**Frontend (package.json):**
```bash
# 1. Detener servicios
docker-compose down

# 2. Reconstruir frontend
docker-compose build frontend

# 3. Levantar servicios
docker-compose up -d
```

### Poblar Base de Datos con Datos de Prueba

```bash
# Método 1: Django admin (http://localhost:8000/admin/)
docker-compose exec backend python manage.py createsuperuser

# Método 2: Shell interactivo
docker-compose exec backend python manage.py shell

# Método 3: Cargar fixtures (si existen)
docker-compose exec backend python manage.py loaddata datos_prueba.json
```

## Solución de Problemas

### Error: "Port already in use"

```bash
# Ver qué está usando el puerto
netstat -ano | findstr :8000

# Detener proceso en Windows
taskkill /PID <PID> /F

# O cambiar el puerto en docker-compose.yml
ports:
  - "8001:8000"  # Usar 8001 en lugar de 8000
```

### Error: "Database connection refused"

```bash
# Verificar que el contenedor de db esté corriendo
docker-compose ps

# Reiniciar servicios con orden correcto
docker-compose down
docker-compose up -d db
docker-compose up -d backend
docker-compose up -d frontend
```

### Error: "No migrations to apply"

```bash
# Crear migraciones manualmente
docker-compose exec backend python manage.py makemigrations

# Aplicar migraciones
docker-compose exec backend python manage.py migrate
```

### Ver más detalles de un error

```bash
# Ejecutar sin modo detached para ver errores en tiempo real
docker-compose up

# O inspeccionar logs con más detalles
docker-compose logs --tail=100 backend
```

### Resetear Base de Datos Completamente

```bash
# 1. Detener y eliminar todo
docker-compose down -v

# 2. Levantar de nuevo (crea DB nueva)
docker-compose up --build
```

## Variables de Entorno

Edita el archivo `.env` en la raíz del proyecto para cambiar configuraciones:

```env
# Base de datos
DB_HOST=db
DB_NAME=smartpharm_db
DB_USER=smartpharm_user
DB_PASSWORD=123456

# Django
DEBUG=True
SECRET_KEY=tu-secret-key-aqui
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost,http://localhost:80
```

## Estructura de Archivos Docker

```
SmartPharm/
├── Dockerfile                      # Dockerfile del backend
├── docker-compose.yml             # Orquestación de servicios
├── .dockerignore                  # Archivos a ignorar en backend
├── requirements.txt               # Dependencias Python
├── smartpharm-frontend/
│   ├── Dockerfile                 # Dockerfile del frontend
│   ├── nginx.conf                 # Configuración de Nginx
│   └── .dockerignore             # Archivos a ignorar en frontend
└── DOCKER.md                      # Esta guía
```

## Comandos Rápidos de Referencia

```bash
# Levantar todo
docker-compose up -d

# Reconstruir todo
docker-compose up --build

# Ver logs
docker-compose logs -f

# Detener todo
docker-compose down

# Estado de contenedores
docker-compose ps

# Ejecutar comando en backend
docker-compose exec backend python manage.py <comando>

# Acceder a PostgreSQL
docker-compose exec db psql -U smartpharm_user -d smartpharm_db

# Reiniciar servicio
docker-compose restart <servicio>

# Eliminar todo y reconstruir
docker-compose down -v && docker-compose up --build
```

## Producción

Para desplegar en producción, considera:

1. Cambiar contraseñas en `.env`
2. Configurar `DEBUG=False` en Django
3. Usar HTTPS con certificados SSL
4. Configurar variables de entorno seguras
5. Usar volúmenes persistentes para datos
6. Configurar backups automáticos de PostgreSQL
7. Implementar logs centralizados

## Soporte

Si encuentras problemas:

1. Revisa los logs: `docker-compose logs -f`
2. Verifica que Docker Desktop esté corriendo
3. Asegúrate de estar en el directorio correcto
4. Revisa la documentación: `ENDPOINTS.md` y `ROADMAP.md`

---

**Última actualización:** Octubre 2025
