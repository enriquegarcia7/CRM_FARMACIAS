# SmartPharm Frontend

Sistema de gestión farmacéutica inteligente desarrollado con React + Vite.

## Características Implementadas

### 1. Dashboard Interactivo
- Visualización de ventas totales y mensuales
- Gráficos con Recharts (líneas y barras)
- Top 10 productos más vendidos
- Actualización automática cada 30 segundos
- Tarjetas de estadísticas con iconos

### 2. Inventario de Productos
- Lista completa con código, descripción, categoría
- Stock actual vs stock mínimo
- Filtros por nivel de stock (crítico, bajo, normal)
- Búsqueda en tiempo real
- Alertas visuales con colores

### 3. Gestión de Clientes
- Clasificación automática: Frecuentes (≥5 compras) / Normales (<5 compras)
- Historial de compras y montos totales
- Filtros y búsqueda avanzada
- Botón para envío masivo de ofertas
- Indicadores de elegibilidad para ofertas

### 4. Sugerencias de Compra Inteligente
- **Por Bajo Stock:** Productos críticos que requieren reposición
- **Estacionales (ML):** Predicciones basadas en temporadas
- **Epidemiológicas (MINSAL):** Basadas en alertas sanitarias
- **Ofertas de Laboratorios (ETL):** Carga y procesamiento de Excel/PDF
- Generación de órdenes de compra
- Indicadores de prioridad y confianza

## Tecnologías Utilizadas

- **React 18** - Framework principal
- **Vite** - Build tool y dev server
- **React Router DOM** - Navegación
- **Recharts** - Gráficos interactivos
- **Tailwind CSS** - Estilos
- **Lucide React** - Iconos
- **Axios** - Cliente HTTP

## Instalación

```bash
# Instalar dependencias
npm install

# Ejecutar en modo desarrollo
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview
```

## Estructura del Proyecto

```
src/
├── components/
│   ├── layout/
│   │   └── Layout.jsx          # Layout principal con sidebar
│   └── common/                 # Componentes reutilizables
├── pages/
│   ├── Dashboard/
│   │   └── Dashboard.jsx       # Página principal con gráficos
│   ├── Inventory/
│   │   └── Inventory.jsx       # Gestión de inventario
│   ├── Customers/
│   │   └── Customers.jsx       # Gestión de clientes
│   └── PurchaseSuggestions/
│       └── PurchaseSuggestions.jsx  # Sugerencias inteligentes
├── services/
│   └── api.js                  # Configuración de Axios y endpoints
├── utils/                      # Funciones utilitarias
├── App.jsx                     # Configuración de rutas
└── main.jsx                    # Punto de entrada
```

## Configuración de API

El frontend está configurado para conectarse al backend Django en:

```javascript
const API_BASE_URL = 'http://localhost:8000/api';
```

Para cambiar la URL, edita `src/services/api.js`.

## Endpoints API Requeridos

### Implementados en Backend:
- `GET /api/clientes/` - Lista de clientes
- `GET /api/transacciones/` - Lista de transacciones

### Por Implementar en Backend:
- `GET /api/productos/` - Lista de productos
- `GET /api/dashboard/stats/` - Estadísticas del dashboard
- `GET /api/dashboard/top-products/` - Top productos
- `GET /api/sugerencias/` - Sugerencias de compra
- `GET /api/ofertas/` - Ofertas de laboratorios
- `POST /api/ofertas/procesar/` - Procesar archivo de ofertas
- `GET /api/clientes/frecuentes/` - Clientes frecuentes

Ver `ROADMAP.md` en la raíz del proyecto para detalles de implementación.

## Datos de Prueba

Actualmente el frontend usa datos simulados. Para conectar con el backend real:

1. Asegúrate de que Django esté corriendo en `http://localhost:8000`
2. Los datos se cargarán automáticamente desde las APIs
3. Los datos simulados serán reemplazados por datos reales

## Scripts Disponibles

- `npm run dev` - Inicia servidor de desarrollo (http://localhost:5173)
- `npm run build` - Crea build de producción
- `npm run preview` - Preview del build de producción
- `npm run lint` - Ejecuta ESLint

## Próximos Pasos

Ver `ROADMAP.md` para:
- Implementación de Machine Learning
- Sistema ETL para ofertas
- Integración con API MINSAL
- Sistema de envío de correos
- Y más...

## Navegación

- `/` - Dashboard principal
- `/inventario` - Gestión de inventario
- `/clientes` - Gestión de clientes
- `/sugerencias` - Sugerencias de compra

## Soporte

Para más información, consulta la documentación completa en `ROADMAP.md`.
