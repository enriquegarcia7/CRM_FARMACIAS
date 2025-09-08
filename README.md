# CRM_FARMACIAS
PROYECTO CAPTONE DUOC UC Grupo 5
# 🏥 SmartPharm - Plataforma Inteligente para Farmacias

Una solución integral que automatiza el abastecimiento, inventario y gestión de clientes para farmacias independientes en Chile.

## 🎯 Problema

Las farmacias pequeñas enfrentan desafíos operativos críticos:
- **Gestión manual**: Descarga manual de ventas, comparación con stock, revisión de múltiples listas de proveedores
- **Datos fragmentados**: Sistemas no integrados (ventas, inventario, proveedores)
- **Ineficiencias**: Quiebres de stock, sobrecostos de adquisición, oportunidades perdidas de fidelización

## 💡 Solución

Plataforma que combina automatización inteligente con análisis predictivo:

### Componentes Core
- **🔄 Ingesta Automatizada**: Normalización de datos desde sistemas POS y listas de proveedores
- **📊 Catálogo Maestro**: Unificación de códigos y productos entre proveedores
- **🤖 ML Engine**: Pronóstico de demanda y detección de patrones de compra
- **📦 Gestión de Inventario**: Alertas automáticas y prevención de quiebres
- **🛒 Automatización de Pedidos**: Generación y envío directo a proveedores
- **👥 CRM Inteligente**: Segmentación y campañas personalizadas
- **📈 Business Intelligence**: Dashboards de rendimiento y ROI

## 🛠️ Stack Tecnológico

```
Backend:     Python (FastAPI, Pandas, SQLAlchemy)
ML/AI:       scikit-learn, Prophet, TensorFlow
Frontend:    React/Next.js, TypeScript
Database:    PostgreSQL + Redis (cache)
BI:          Metabase / Power BI
DevOps:      Docker, GitHub Actions
```

## 📊 Beneficios Proyectados

> ⚠️ **Nota**: Métricas basadas en estimaciones iniciales, requieren validación empírica

- **Económicos**: 3-8% ahorro en costos de adquisición
- **Operacionales**: 50% reducción en quiebres de stock
- **Tiempo**: 60% menos tiempo en gestión administrativa
- **Ventas**: Incremento en recurrencia de clientes frecuentes

## 🚀 Roadmap

### Fase 1: MVP (3 meses)
- [ ] Integración básica con sistemas POS
- [ ] Catálogo de productos normalizado
- [ ] Alertas de stock bajo
- [ ] Dashboard básico

### Fase 2: Inteligencia (6 meses)
- [ ] Motor de predicción de demanda
- [ ] Automatización de pedidos
- [ ] Segmentación básica de clientes

### Fase 3: Optimización (9 meses)
- [ ] ML avanzado para pronósticos
- [ ] CRM completo con campañas
- [ ] Analytics avanzados

## 🏗️ Estructura del Proyecto

```
smartpharm/
├── backend/
│   ├── api/          # FastAPI endpoints
│   ├── ml/           # Modelos de ML
│   ├── etl/          # Procesamiento de datos
│   └── database/     # Modelos y migraciones
├── frontend/
│   ├── components/   # Componentes React
│   ├── pages/        # Páginas Next.js
│   └── hooks/        # Custom hooks
├── data/
│   ├── raw/          # Datos sin procesar
│   ├── processed/    # Datos limpios
│   └── models/       # Modelos entrenados
└── docs/             # Documentación
```

## 🤝 Contribuciones

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles

## 🎯 Estado del Proyecto

🟡 **Proyecto Académico en Desarrollo** - MVP con 3 casos de uso para evaluación académica

### Contexto Académico
- **Datos reales**: Acceso a farmacia local con historial completo
- **Usuario piloto**: Administrador de farmacia en el equipo
- **Enfoque**: Documentación técnica, análisis financiero (ROI, VAN) y MVP funcional

### Casos de Uso MVP (10 semanas)
**Alcance REALISTA para timeline académico:**

**Caso 1: Monitor de Stock Crítico** ⏱️ 3 semanas
- Importar ventas históricas desde Excel/CSV
- Algoritmo simple: promedio móvil para detectar stock bajo
- Alertas automáticas por email/dashboard

**Caso 2: Recomendador Básico de Pedidos** ⏱️ 4 semanas  
- Análisis de ventas últimos 3-6 meses
- Reglas simples: "si vendiste X unidades/mes, pedir Y"
- Interface para aprobar/modificar sugerencias

**Caso 3: Dashboard de Rentabilidad** ⏱️ 2 semanas
- Visualización básica: ventas, márgenes, rotación
- Comparación mes actual vs anterior
- Identificación de productos más/menos rentables

**NO incluye:** ML complejo, automatización de pedidos, CRM avanzado, integración en tiempo real

### Entregables Académicos
- [ ] Documentación técnica completa
- [ ] Análisis financiero (ROI, VAN, TIR)
- [ ] Propuesta de financiamiento
- [ ] MVP con 3 casos de uso funcionales
- [ ] Validación con datos reales

---
