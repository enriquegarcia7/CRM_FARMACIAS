markdown# 🏥 SmartPharm CRM

**Sistema de Gestión Especializado para Farmacias Pequeñas en Chile**

[![Django](https://img.shields.io/badge/Django-5.0-green)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18.3-blue)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://www.postgresql.org/)
[![Estado](https://img.shields.io/badge/Estado-MVP%20Funcional-success)](https://github.com)

> **Proyecto Capstone** - Ingeniería en Informática, Duoc UC 2025

---

## 📌 Descripción

Sistema CRM especializado que combina análisis de datos, machine learning y gestión de clientes para optimizar operaciones farmacéuticas mediante segmentación inteligente, predicción de demanda estacional y análisis de ofertas.

**Proyecto académico**: 70% Business Plan + 30% MVP Técnico

---

## 👥 Equipo

| Rol | Nombre | Responsabilidad |
|-----|--------|-----------------|
| Líder | Enrique García | Análisis financiero y gestión PMI |
| Validador | Daniel Acevedo | Requerimientos del sector (5+ años) |
| Desarrollador | Bastian Hartal | Arquitectura y desarrollo MVP |

---

## 🎯 Funcionalidades Principales

### ✅ Dashboard Analítico
Estadísticas en tiempo real, gráficos de ventas mensuales y top productos

### ✅ Segmentación de Clientes
Clasificación automática por frecuencia de compra y análisis de historial

### ✅ Control de Inventario
Alertas de stock (crítico/bajo/normal) y gestión de 15 productos farmacéuticos

### ✅ Sugerencias Inteligentes
- **Bajo Stock**: Reposición automática
- **Estacionales**: Predicciones ML para temporadas
- **Epidemiológicas**: Alertas MINSAL
- **Ofertas**: Comparador de precios de laboratorios

---

## 🛠️ Stack Tecnológico
```
Frontend:  React 18.3 + Vite + TailwindCSS + Recharts
Backend:   Django 5.0.4 + Django REST Framework 3.16
Database:  PostgreSQL 15 (8 tablas + 2 vistas materializadas)
Deploy:    Docker Compose
```

**Arquitectura**: API REST con 19 endpoints

---

## 🚀 Instalación Rápida

### Prerequisitos
- Docker Desktop
- Git

### Pasos
```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/smartpharm-crm.git
cd smartpharm-crm

# 2. Levantar servicios
docker-compose up -d

# 3. Aplicar migraciones (primera vez)
docker exec smartpharm_backend python manage.py migrate

# 4. Poblar base de datos con datos de prueba
docker exec smartpharm_backend python manage.py seed_data

# 5. Acceder a la aplicación
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000/admin
```

**Credenciales Admin**: `bhartal` / `123456`

---

## 📊 Estado del Proyecto

### ✅ Completado (85%)
- [x] API REST completa (19 endpoints)
- [x] 4 módulos frontend funcionando
- [x] Base de datos con esquema completo
- [x] Sistema de alertas y sugerencias
- [x] Gráficos y dashboards

### 🚧 Pendiente (15%)
- [ ] Autenticación JWT
- [ ] Tests unitarios
- [ ] Exportación de reportes

---

## 🔧 Comandos Útiles
```bash
# Ver logs
docker logs -f smartpharm_backend

# Acceder a PostgreSQL
docker exec -it smartpharm_db psql -U smartpharm_user -d smartpharm_db

# Re-poblar base de datos
docker exec smartpharm_backend python manage.py seed_data

# Detener servicios
docker-compose down
```

---

## 📚 Datos Generados

Al ejecutar `seed_data`:
- 5 Proveedores farmacéuticos
- 15 Productos (Paracetamol, Ibuprofeno, Amoxicilina, etc.)
- 15 Clientes con historial de compras
- ~180 Ventas históricas (enero-octubre 2025)
- 15 Ofertas activas de laboratorios
- 20 Sugerencias de compra

---

## 🎓 Competencias Aplicadas

✅ Análisis de negocio y propuesta de solución informática  
✅ Gestión de proyectos con metodología PMI  
✅ Desarrollo de software con arquitectura API REST  
✅ Modelado de datos escalable (PostgreSQL)  
✅ Transformación de datos para toma de decisiones  

---

## 📑 Entregables Académicos

**Documentación (70%)**:
- Business Plan Ejecutivo
- Análisis Financiero (ROI, VAN, TIR)
- Plan de Gestión PMI

**MVP Técnico (30%)**:
- 4 módulos funcionales
- 19 endpoints API REST
- Base de datos con datos reales

---

## 📄 Documentación Adicional

- [Informe de Refactorización](./INFORME_REFACTORIZACION_SMARTPHARM.md)
- [Esquema de Base de Datos](./database_schema.sql)

---

## 📜 Licencia

MIT License

---

**Duoc UC 2025 - Ingeniería en Informática**  
*Proyecto de Aplicación de Título*  
**Estado**: ✅ MVP Funcional - Production Ready
