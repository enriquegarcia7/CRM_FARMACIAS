# SmartPharm CRM

**Sistema de Gestión de Clientes Especializado para Farmacias**

---

## 📋 Descripción

SmartPharm CRM es una plataforma integral diseñada específicamente para farmacias pequeñas y medianas en Chile. El sistema combina gestión de clientes, inventario inteligente y análisis predictivo para optimizar las operaciones farmacéuticas.

### Características Principales

- 🏥 **Gestión de Clientes Farmacéuticos**: Segmentación avanzada por tipo de medicamento y frecuencia de compra
- 📊 **Dashboard Analítico**: Visualización en tiempo real de métricas clave del negocio
- 💊 **Gestión de Inventario**: Control de stock con alertas automáticas
- 🎯 **Sugerencias de Compra Inteligentes**: Basadas en patrones de consumo y ofertas de laboratorios
- 📈 **Análisis Predictivo**: Anticipación de demanda estacional

---

## 🏗️ Arquitectura del Proyecto

```
sistema_aplicacion_V2/
├── Backend_Django/          # API REST - Django + Django REST Framework
│   ├── core/               # App principal con modelos y lógica de negocio
│   ├── manage.py           # Comando de administración de Django
│   ├── requirements.txt    # Dependencias de Python
│   ├── Dockerfile          # Imagen Docker del backend
│   └── settings.py         # Configuración de Django
│
├── Frontend_React/          # Interfaz de usuario - React + Vite
│   ├── src/                # Código fuente
│   │   ├── components/     # Componentes reutilizables
│   │   ├── pages/          # Páginas de la aplicación
│   │   └── services/       # Servicios y llamadas API
│   ├── package.json        # Dependencias de Node.js
│   ├── Dockerfile          # Imagen Docker del frontend
│   └── vite.config.js      # Configuración de Vite
│
├── docker-compose.yml       # Orquestación de servicios
├── .env                     # Variables de entorno (NO commitear)
├── .env.example             # Plantilla de variables de entorno
├── .gitignore               # Archivos ignorados por Git
└── README.md                # Este archivo
```

---

## 🛠️ Stack Tecnológico

### Backend
- **Framework**: Django 5.x + Django REST Framework
- **Base de Datos**: PostgreSQL 15
- **Autenticación**: Token-based authentication
- **Servidor**: Gunicorn

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **UI Library**: TailwindCSS
- **Gráficos**: Recharts
- **Routing**: React Router v6
- **Estado**: Redux Toolkit

### DevOps
- **Containerización**: Docker + Docker Compose
- **Base de Datos**: PostgreSQL en contenedor
- **Proxy**: Nginx (para el frontend en producción)

---

## 🚀 Inicio Rápido

### Prerrequisitos

- Docker >= 20.10
- Docker Compose >= 2.0
- Git

### Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd sistema_aplicacion_V2
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

3. **Levantar los servicios con Docker**
   ```bash
   docker-compose up --build
   ```

4. **Acceder a la aplicación**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - Admin Django: http://localhost:8000/admin

### Credenciales por Defecto

- **Usuario**: bhartal
- **Email**: bastianhartal@gmail.com
- **Contraseña**: 123456

> ⚠️ **IMPORTANTE**: Cambiar estas credenciales en producción

---

## 📦 Comandos Útiles

### Docker

```bash
# Levantar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Reconstruir imágenes
docker-compose build --no-cache

# Ejecutar migraciones
docker-compose exec backend python manage.py migrate

# Crear superusuario manualmente
docker-compose exec backend python manage.py createsuperuser

# Acceder al shell de Django
docker-compose exec backend python manage.py shell
```

### Desarrollo Local (sin Docker)

#### Backend
```bash
cd Backend_Django
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

#### Frontend
```bash
cd Frontend_React
npm install
npm run dev
```

---

## 📚 Documentación Adicional

- [Endpoints de la API](Backend_Django/ENDPOINTS.md)
- [Guía de Docker](Backend_Django/DOCKER.md)
- [Roadmap del Proyecto](Backend_Django/ROADMAP.md)

---

## 🧪 Testing

```bash
# Backend - Ejecutar tests
docker-compose exec backend python manage.py test

# Frontend - Ejecutar tests
docker-compose exec frontend npm test
```

---

## 📊 Base de Datos

El proyecto incluye datos de prueba de una farmacia real (anonimizados):

- **Clientes**: ~5,000 registros
- **Productos**: ~2,500 productos farmacéuticos
- **Transacciones**: Datos históricos desde 2022

Para cargar datos iniciales:
```bash
docker-compose exec backend python manage.py import_farmacia
```

---

## 🔐 Seguridad

- Las contraseñas se almacenan hasheadas con PBKDF2
- Autenticación basada en tokens
- CORS configurado para desarrollo
- Variables sensibles en archivo `.env` (no versionado)

> ⚠️ **Para Producción**:
> - Cambiar `DJANGO_DEBUG=False`
> - Usar contraseñas seguras
> - Configurar ALLOWED_HOSTS correctamente
> - Usar HTTPS

---

## 🤝 Contribución

Este proyecto es parte del Capstone de Ingeniería en Informática - Duoc UC 2025

### Equipo
- **Bastian Hartal** - Desarrollo MVP Técnico
- **Enrique García** - Análisis Financiero y Gestión PMI
- **Daniel Acevedo** - Validación de Mercado y Requerimientos

---

## 📝 Licencia

MIT License - Ver archivo LICENSE para más detalles

---

## 📞 Contacto

Para consultas sobre el proyecto:
- Email: bastianhartal@gmail.com
- Institución: Duoc UC - Sede Antonio Varas

---

**Proyecto Capstone 2025** | Ingeniería en Informática | Duoc UC
