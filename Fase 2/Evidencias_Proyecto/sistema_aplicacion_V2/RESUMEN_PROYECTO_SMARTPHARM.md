# SmartPharm CRM - Sistema de Gestión para Farmacias

## 📋 RESUMEN EJECUTIVO

**SmartPharm CRM** es un sistema integral de gestión para farmacias que combina análisis de clientes, gestión de inventario inteligente, procesamiento automático de ofertas de laboratorios mediante ETL, y predicción de demanda estacional utilizando Machine Learning.

**Versión**: 2.0
**Stack**: Django REST Framework + React + PostgreSQL + Docker
**Características Principales**: CRM Clientes, Inventario Dinámico, ETL Automático, ML Predictivo

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Arquitectura General
```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                         │
│  - Dashboard    - Clientes    - Inventario    - Ofertas     │
│  - Ventas       - Predicción Estacional       - ETL Admin   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────────────┐
│              BACKEND (Django REST Framework)                 │
│  ┌──────────────┬──────────────┬──────────────────────────┐ │
│  │  REST APIs   │  ML Service  │  ETL Service (Celery)    │ │
│  │              │              │                          │ │
│  │ - Clientes   │ - Random     │ - Gmail API              │ │
│  │ - Productos  │   Forest     │ - PDF/Excel Parser       │ │
│  │ - Ventas     │ - Predicción │ - Offer Processing       │ │
│  │ - Ofertas    │   Estacional │ - Background Tasks       │ │
│  └──────────────┴──────────────┴──────────────────────────┘ │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                PostgreSQL Database                           │
│  - Clientes          - Productos/Inventario                 │
│  - Ventas/DetalleVenta    - Ofertas                         │
│  - Sugerencias Compra     - ETL Logs                        │
└─────────────────────────────────────────────────────────────┘
```

### Contenedores Docker
1. **smartpharm_frontend** (Nginx + React)
   - Puerto: 3000
   - Build: Vite production bundle

2. **smartpharm_backend** (Django + Gunicorn)
   - Puerto: 8000
   - Workers: 3 Gunicorn workers

3. **smartpharm_db** (PostgreSQL 15)
   - Puerto: 5432
   - Volumen persistente: postgres_data

4. **Redis** (Para Celery)
   - Puerto: 6379
   - Cache & Message Broker

5. **Celery Worker** (Tareas async)
   - Beat scheduler para ETL automático

---

## 💾 MODELO DE DATOS

### Módulo: Gestión de Clientes

**Cliente**
```python
- id: AutoField (PK)
- rut: CharField(20, unique=True)  # RUT chileno normalizado
- nombre: CharField(200)
- correo: EmailField(unique=True)
- telefono: CharField(20, blank=True)
- direccion: TextField(blank=True)
- fecha_registro: DateTimeField(auto_now_add=True)
```

**Propiedades Calculadas**:
- `total_compras`: Cuenta ventas completadas
- `monto_total`: Suma de todas las ventas
- `ultima_compra`: Fecha de última venta
- `frecuencia`: 'frecuente' si ≥5 compras, 'normal' si <5

### Módulo: Ventas

**Venta**
```python
- id: AutoField (PK)
- tipo_documento: CharField(20)  # 'boleta', 'factura'
- numero: CharField(50)
- cliente: ForeignKey(Cliente)
- fecha: DateField
- total: DecimalField(10,2)
- metodo_pago: CharField(50)
- estado: CharField(20)  # 'completada', 'pendiente', 'anulada'
- hash_unico: CharField(64, unique=True)  # SHA256 para deduplicación
```

**DetalleVenta**
```python
- id: AutoField (PK)
- venta: ForeignKey(Venta)
- producto: ForeignKey(Producto)
- cantidad: IntegerField
- precio_unitario: DecimalField(10,2)
- subtotal: DecimalField(10,2)
```

### Módulo: Inventario

**Categoria**
```python
- id: AutoField (PK)
- nombre: CharField(100, unique=True)
- descripcion: TextField(blank=True)
- icono: CharField(50, blank=True)
- activa: BooleanField(default=True)
```

**Producto** (Inventario Físico)
```python
- id: AutoField (PK)
- codigo: CharField(50, unique=True)
- nombre: CharField(200)
- descripcion: CharField(200, blank=True)
- categoria: ForeignKey(Categoria, null=True)
- stock_actual: IntegerField(default=0)
- stock_minimo: IntegerField(default=10)
- precio_venta: DecimalField(10,2)
- precio_costo: DecimalField(10,2)
- proveedor_principal: ForeignKey(Proveedor, null=True)
- codigo_barras: CharField(100, blank=True)
- activo: BooleanField(default=True)
```

**Propiedades Calculadas Dinámicas**:
- `bajo_stock`: bool - stock_actual < stock_minimo
- `stock_minimo_dinamico`: int - Cálculo ML basado en ventas históricas
- `metricas_stock`: dict - Demanda diaria, días cobertura, nivel riesgo

**ProductoCatalogo** (Catálogo de Proveedores)
```python
- id: AutoField (PK)
- codigo: CharField(100, unique=True)
- nombre: CharField(300)
- descripcion: TextField
- categoria: ForeignKey(Categoria, null=True)
- proveedor: ForeignKey(Proveedor)
- activo: BooleanField(default=True)
```

### Módulo: Ofertas de Laboratorios

**Laboratorio**
```python
- id: AutoField (PK)
- nombre: CharField(200, unique=True)
- rut: CharField(20, blank=True)
- direccion: TextField(blank=True)
- telefono: CharField(20, blank=True)
- email: EmailField(blank=True)
- pais: CharField(100, default='Chile')
- activo: BooleanField(default=True)
```

**OfertaLaboratorio**
```python
- id: AutoField (PK)
- producto_catalogo: ForeignKey(ProductoCatalogo)
- laboratorio: ForeignKey(Laboratorio)
- precio_normal: DecimalField(10,2)
- precio_oferta: DecimalField(10,2)
- descuento: DecimalField(5,2)  # Porcentaje
- fecha_inicio: DateField
- fecha_fin: DateField
- activa: BooleanField(default=True)
- created_at: DateTimeField(auto_now_add=True)
```

**Propiedades**:
- `ahorro`: precio_normal - precio_oferta

### Módulo: ETL

**ETLLog**
```python
- id: AutoField (PK)
- fecha_ejecucion: DateTimeField
- emails_procesados: IntegerField
- adjuntos_descargados: IntegerField
- ofertas_extraidas: IntegerField
- ofertas_insertadas: IntegerField
- ofertas_actualizadas: IntegerField
- errores: IntegerField
- duracion_segundos: FloatField
- exitoso: BooleanField
```

**ArchivoProcesado**
```python
- id: AutoField (PK)
- etl_log: ForeignKey(ETLLog)
- nombre_archivo: CharField(255)
- hash_archivo: CharField(64)  # SHA256 para deduplicación
- tamano_bytes: BigIntegerField
- ofertas_extraidas: IntegerField
- fecha_procesamiento: DateTimeField
- email_id: CharField(255)
- email_subject: CharField(500)
```

### Módulo: Sugerencias de Compra

**SugerenciaCompra**
```python
- id: AutoField (PK)
- producto: ForeignKey(Producto)
- tipo: CharField(20)  # 'bajo_stock', 'prediccion_ml', 'estacional'
- cantidad_sugerida: IntegerField
- prioridad: CharField(20)  # 'baja', 'media', 'alta', 'critica'
- razon: TextField
- confianza_ml: DecimalField(5,2, null=True)  # 0-100%
- fuente_datos: CharField(50)  # 'ventas_historicas', 'modelo_ml'
- fecha_creacion: DateTimeField(auto_now_add=True)
- procesada: BooleanField(default=False)
```

### Módulo: Mapeo Productos-Proveedores

**ProductoProveedorMapping**
```python
- id: AutoField (PK)
- producto_interno: ForeignKey(Producto)
- codigo_proveedor: CharField(100)
- proveedor: ForeignKey(Proveedor)
- nombre_en_catalogo: CharField(300)
- activo: BooleanField(default=True)
- confianza: DecimalField(5,2, default=100.00)  # 0-100%
- fecha_mapeo: DateTimeField(auto_now_add=True)
- mapeado_por: CharField(50)  # 'manual', 'automatico', 'ml'
- notas: TextField(blank=True)
```

---

## 🔌 APIs REST - ENDPOINTS PRINCIPALES

### Base URL: `http://localhost:8000/api/`

### 1. Clientes (`/clientes/`)

**GET /clientes/** - Listar clientes (paginado)
- Query params:
  - `page`: int (default: 1)
  - `page_size`: int (default: 50)
- Response:
```json
{
  "count": 2848,
  "next": "http://localhost:8000/api/clientes/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "rut": "12345678-9",
      "nombre": "Juan Pérez",
      "correo": "juan@email.com",
      "total_compras": 15,
      "monto_total": 450000.00,
      "ultima_compra": "2025-09-30",
      "frecuencia": "frecuente"
    }
  ]
}
```

**GET /clientes/stats/** - Estadísticas globales
```json
{
  "total_clientes": 2848,
  "clientes_frecuentes": 2683,
  "clientes_normales": 165,
  "elegibles_ofertas": 2683
}
```

**GET /clientes/frecuentes/** - Solo clientes frecuentes (≥5 compras)

**POST /clientes/** - Crear cliente
**PUT /clientes/{id}/** - Actualizar cliente
**DELETE /clientes/{id}/** - Eliminar cliente

---

### 2. Productos/Inventario (`/productos/`)

**GET /productos/** - Listar productos (paginado)
- Query params:
  - `page`: int
  - `page_size`: int (default: 50)
  - `search`: string (busca en código y nombre)
  - `filtro_stock`: 'bajo' | 'normal' | ''
- Response:
```json
{
  "count": 4700,
  "results": [
    {
      "id": 1,
      "codigo": "1",
      "nombre": "Pastilla de carbon tira",
      "stock_actual": 69,
      "stock_minimo": 10,
      "stock_minimo_dinamico": 11,
      "metricas_stock": {
        "demanda_promedio_diaria": 1.25,
        "total_vendido_90dias": 20,
        "dias_cobertura": 55.2,
        "nivel_riesgo": "bajo"
      },
      "precio_venta": "1261.00",
      "bajo_stock": false
    }
  ]
}
```

**GET /productos/low-stock/** - Productos con bajo stock

**GET /productos/top-selling/** - Top productos más vendidos
- Query param: `limit` (default: 10)

**GET /productos/ultima-carga/** - Fecha de última actualización de inventario

**POST /productos/cargar_excel/** - Cargar inventario desde Excel
- Body: FormData con campo `archivo` (file)
- Expected columns: CODIGO, PRODUCTO, PREC UNITARIO, PREC UNIDADES, STOCK

---

### 3. Ventas (`/ventas/`)

**GET /ventas/** - Listar ventas
**GET /ventas/{id}/** - Detalle de venta
**GET /ventas/stats/** - Estadísticas de ventas
**POST /ventas/** - Registrar nueva venta

---

### 4. Dashboard (`/dashboard/`)

**GET /dashboard/stats/** - Estadísticas principales
```json
{
  "total_ventas": 808153801.0,
  "ventas_mes": 14054047.0,
  "productos_stock": 4700,
  "clientes_activos": 2847
}
```

**GET /dashboard/sales/** - Ventas mensuales para gráficos
```json
[
  {"mes": "2025-01", "total": 15000000},
  {"mes": "2025-02", "total": 18000000}
]
```

**GET /dashboard/top-products/** - Top 10 productos para dashboard
```json
[
  {
    "producto__descripcion": "GENIOL SOBRE LIMONADA",
    "cantidad": 14919,
    "ventas": 7400000
  }
]
```

---

### 5. Ofertas de Laboratorios (`/ofertas/`)

**GET /ofertas/por_laboratorio/** - Ofertas agrupadas por laboratorio (paginado)
- Query params:
  - `page`: int
  - `page_size`: int
  - `laboratorio`: string (filtro)
  - `activas`: bool (default: true)
  - `search`: string
- Response:
```json
{
  "count": 1250,
  "results": [
    {
      "id": 1,
      "producto_nombre": "Paracetamol 500mg",
      "laboratorio_nombre": "Mediven",
      "precio_normal": "5000.00",
      "precio_oferta": "3500.00",
      "descuento": "30.00",
      "ahorro": "1500.00",
      "fecha_inicio": "2025-11-01",
      "fecha_fin": "2025-11-30",
      "activa": true
    }
  ]
}
```

**GET /ofertas/laboratorios/** - Lista de laboratorios únicos

**POST /ofertas/procesar/** - Procesar archivo de ofertas (Excel/PDF)
- Body: FormData con campo `archivo`

---

### 6. ETL (`/etl/`)

**POST /etl/run/** - Ejecutar ETL manual
- Body:
```json
{
  "days_back": 5,
  "strict_mode": false
}
```

**GET /etl/logs/** - Historial de ejecuciones ETL
```json
[
  {
    "id": 1,
    "fecha_ejecucion": "2025-11-04T10:30:00Z",
    "emails_procesados": 15,
    "ofertas_extraidas": 450,
    "ofertas_insertadas": 420,
    "exitoso": true,
    "duracion_segundos": 125.5
  }
]
```

**GET /etl/status/** - Estado actual del ETL
**GET /etl/progress/** - Progreso en tiempo real (Server-Sent Events)
**GET /etl/diagnostic/** - Diagnóstico de conexión Gmail

---

### 7. Predicción Estacional (`/seasonal/`)

**POST /seasonal/predict/** - Predecir demanda para mes específico
- Body:
```json
{
  "categoria": "ANTIGRIPAL",
  "mes": 6,
  "año": 2026
}
```
- Response:
```json
{
  "categoria": "ANTIGRIPAL",
  "mes": 6,
  "año": 2026,
  "prediccion_transacciones": 450,
  "historico": [...],
  "features_usadas": {
    "lag_1_mes": 420,
    "lag_3_meses": 380,
    "promedio_movil_3m": 400
  },
  "interpretacion": {
    "tendencia": "ALTA",
    "variacion_vs_promedio": 12.5
  }
}
```

**GET /seasonal/year/** - Predicción anual completa
- Query params:
  - `categoria`: string (requerido)
  - `año`: int (default: año_actual + 1)
- Response:
```json
{
  "categoria": "ANTIGRIPAL",
  "año": 2026,
  "predicciones": [
    {"mes": 1, "mes_nombre": "Enero", "prediccion": 231},
    {"mes": 2, "mes_nombre": "Febrero", "prediccion": 231},
    ...
  ],
  "total_anual_proyectado": 2805
}
```

**GET /seasonal/categories/** - Categorías disponibles en el modelo ML
```json
{
  "categorias": ["ANALGESICO", "ANTIGRIPAL", "ANTIHISTAMINICO", ...],
  "total": 126,
  "fuente": "Modelo ML entrenado"
}
```

---

### 8. Gmail Auth (`/gmail/auth/`)

**GET /gmail/auth/status/** - Estado de autenticación Gmail
**GET /gmail/auth/start/** - Iniciar flujo OAuth2
**DELETE /gmail/auth/revoke/** - Revocar credenciales

---

## 🤖 MÓDULOS DE MACHINE LEARNING

### 1. Predicción de Demanda Estacional

**Archivo**: `Backend_Django/core/ml_service.py`

**Modelo**: Random Forest Regressor (126 categorías farmacéuticas)

**Archivos del Modelo**:
- `ml_models/modelo_prediccion_estacional.pkl` (Random Forest entrenado)
- `ml_models/label_encoder_categorias.pkl` (Encoder de categorías)

**Features de Entrada**:
1. `mes` (1-12)
2. `año`
3. `categoria_encoded` (0-125)
4. `trans_lag_1` - Transacciones del mes anterior
5. `trans_lag_3` - Transacciones hace 3 meses
6. `trans_lag_6` - Transacciones hace 6 meses
7. `trans_lag_12` - Transacciones hace 12 meses
8. `trans_ma_3` - Promedio móvil 3 meses

**Categorías Soportadas**: 126 categorías farmacéuticas incluyendo:
- ANALGESICO, ANALGESICO-ANTIINFLAMATORIO, ANTIGRIPAL
- ANTIHISTAMINICO, ANTIBIOTICO OFTALMICO, BRONCODILATADOR
- HIPOTENSORES, ANTIDIABETICO, ANTIULCEROSO
- [Ver lista completa en `/seasonal/categories/`]

**Uso en Stock Dinámico**:
El modelo se integra automáticamente en el cálculo de stock mínimo dinámico para productos con categorías válidas.

---

### 2. Stock Mínimo Dinámico

**Archivo**: `Backend_Django/core/stock_service.py`

**Algoritmo**: Combina análisis estadístico con predicción ML

**Fórmula Base**:
```
Stock Mínimo = (Demanda Promedio Diaria × Lead Time) + Stock de Seguridad
Stock de Seguridad = Z-score × σ × √Lead Time
```

**Parámetros**:
- Lead Time: 7 días
- Nivel de Servicio: 95% (Z-score = 1.65)
- Período histórico: 90 días

**Factor Estacional ML** (Nuevo):
```python
# Predicción ML del próximo mes
prediccion_proxima = seasonal_service.predict(...)

# Factor basado en predicción vs histórico
factor_ml = (prediccion_proxima / 30) / promedio_historico

# Combinar ML (60%) + Tendencia básica (40%)
factor_combinado = (factor_ml * 0.6) + (factor_tendencia * 0.4)

# Stock final ajustado por estacionalidad
stock_minimo_final = stock_base × factor_combinado
```

**Métricas Calculadas**:
```python
{
  "demanda_promedio_diaria": 1.25,
  "total_vendido_90dias": 20,
  "dias_cobertura": 55.2,
  "nivel_riesgo": "bajo"  # critico/alto/medio/bajo
}
```

**Clasificación de Riesgo**:
- **Crítico**: < 7 días de cobertura
- **Alto**: 7-14 días
- **Medio**: 14-30 días
- **Bajo**: > 30 días

---

## 🔄 SISTEMA ETL - PROCESAMIENTO DE OFERTAS

### Arquitectura ETL

**Componentes**:
1. **Gmail API Client** - Conexión OAuth2 con Gmail
2. **Email Processor** - Extracción de adjuntos
3. **File Parsers** - Excel y PDF
4. **Offer Processor** - Normalización de datos
5. **Celery Tasks** - Ejecución asíncrona

### Flujo del ETL

```
┌─────────────────────────────────────────────────────────────┐
│ 1. EXTRACCIÓN - Gmail API                                    │
│    - Consultar correos de laboratorios (últimos N días)     │
│    - Filtros: remitentes autorizados, keywords              │
│    - Descargar adjuntos (Excel/PDF)                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ 2. PARSEO - Archivos                                         │
│    Excel Parser:                                             │
│    - Detectar headers automáticamente                       │
│    - Normalizar columnas (codigo, producto, precio, etc)    │
│    - Validar formato de precios y fechas                    │
│                                                              │
│    PDF Parser:                                               │
│    - Extracción con PyPDF2/pdfplumber                       │
│    - Regex patterns para identificar ofertas                │
│    - OCR fallback para PDFs escaneados                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ 3. TRANSFORMACIÓN                                            │
│    - Normalizar nombres de productos                        │
│    - Calcular descuentos (%)                                │
│    - Validar rangos de fechas                               │
│    - Deduplicación por hash de archivo                      │
│    - Mapeo producto_proveedor → producto_interno            │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ 4. CARGA - Base de Datos                                     │
│    - Insertar/actualizar ProductoCatalogo                   │
│    - Insertar/actualizar OfertaLaboratorio                  │
│    - Registrar ETLLog y ArchivoProcesado                    │
│    - Actualizar mappings producto-proveedor                 │
└─────────────────────────────────────────────────────────────┘
```

### Parsers Implementados

**Excel Parser** (`core/parsers/excel_parser.py`):
```python
Columnas Reconocidas:
- CODIGO / COD / CODIGO_PRODUCTO / SKU
- PRODUCTO / DESCRIPCION / ITEM / NOMBRE
- PRECIO / PRECIO_UNITARIO / PREC_UNITARIO / VALOR
- PRECIO_OFERTA / PRECIO_PROMO / OFERTA
- STOCK (opcional)
- FECHA_INICIO / FECHA_FIN (opcional)

Formatos Soportados:
- .xlsx, .xls
- Headers en cualquier fila (búsqueda automática)
- Precios con $ o sin símbolo
- Fechas en formato chileno o ISO
```

**PDF Parser** (`core/parsers/pdf_parser.py`):
```python
Estrategias:
1. Extracción de texto directo (PyPDF2)
2. Extracción con layout (pdfplumber)
3. Regex patterns para ofertas:
   - Código: \d{4,12}
   - Precio: \$?\s*\d+[\.,]?\d*
   - Descuento: \d+%\s*(off|desc|dscto)

Patrones de Laboratorios:
- Mediven: Formato tabla con códigos EAN
- Socofar: Lista con código-producto-precio
- Provefarma: Excel embebido en PDF
```

### Deduplicación

**Método**: SHA256 hash de archivos
```python
hash_archivo = hashlib.sha256(contenido_archivo).hexdigest()

# Verificar si ya fue procesado
if ArchivoProcesado.objects.filter(hash_archivo=hash_archivo).exists():
    skip_file()
```

### Configuración Celery

**Archivo**: `Backend_Django/config/celery.py`

**Tareas Periódicas**:
```python
CELERY_BEAT_SCHEDULE = {
    'etl-diario': {
        'task': 'core.tasks.run_etl_daily',
        'schedule': crontab(hour=6, minute=0),  # 6:00 AM diario
    },
}
```

**Tareas Disponibles**:
- `run_etl_daily()` - ETL automático diario
- `process_single_email()` - Procesar un email específico
- `cleanup_old_logs()` - Limpiar logs antiguos

---

## 🎨 FRONTEND - PÁGINAS Y COMPONENTES

### Stack Frontend
- **React 18** con Hooks
- **Vite** para build
- **TailwindCSS** para estilos
- **Recharts** para gráficos
- **Lucide Icons** para iconografía
- **Axios** para HTTP requests

### Páginas Implementadas

#### 1. Dashboard (`/`)
**Archivo**: `src/pages/Dashboard/Dashboard.jsx`

**Funcionalidades**:
- 4 KPI Cards:
  - Total Ventas (acumulado)
  - Ventas del Mes (más reciente con datos)
  - Productos en Stock
  - Clientes Activos
- Gráfico de líneas: Ventas Mensuales 2025
- Gráfico de barras: Top 5 Productos Más Vendidos
- Tabla: Top 10 Productos detallado
- Auto-refresh cada 30 segundos

**APIs Consumidas**:
- `GET /api/dashboard/stats/`
- `GET /api/dashboard/sales/`
- `GET /api/dashboard/top-products/`

---

#### 2. Gestión de Clientes (`/clientes`)
**Archivo**: `src/pages/Customers/Customers.jsx`

**Funcionalidades**:
- **Estadísticas Globales** (4 cards):
  - Total Clientes
  - Clientes Frecuentes (≥5 compras)
  - Clientes Normales (<5 compras)
  - Elegibles para Ofertas (>5 compras)

- **Filtros**:
  - Búsqueda por nombre o correo (debounce 500ms)
  - Filtro por tipo: Todos / Frecuentes / Normales

- **Tabla Paginada** (50 por página):
  - Columnas: Tipo, Nombre, Correo, Total Compras, Monto Total, Última Compra, Acciones
  - Badge verde (⭐) para clientes frecuentes
  - Botón "Enviar Oferta" para clientes elegibles
  - Paginación: Primera, Anterior, Siguiente, Última

- **Botón**: "Enviar Ofertas a Clientes Frecuentes" (masivo)

**APIs Consumidas**:
- `GET /api/clientes/?page=X&page_size=50`
- `GET /api/clientes/stats/`

**Estado del Cliente**:
```javascript
{
  id: 1,
  nombre: "Juan Pérez",
  correo: "juan@email.com",
  totalCompras: 15,
  montoTotal: 450000,
  ultimaCompra: "2025-09-30",
  frecuencia: "frecuente"
}
```

---

#### 3. Inventario (`/inventario`)
**Archivo**: `src/pages/Inventory/Inventory.jsx`

**Funcionalidades**:
- **Header**:
  - Botón "Cargar Excel" (modal)
  - Badge con total de productos
  - Fecha/hora de última actualización

- **Filtros**:
  - Búsqueda por código o nombre (debounce 500ms)
  - Filtro de stock: Todos / Bajo stock / Stock normal

- **Tabla Paginada** (50 por página):
  - Código
  - Producto
  - Stock Actual
  - **Stock Mín. (Dinámico)** ← En azul, calculado con ML
    - Si difiere del fijo: muestra "(fijo: X)" en gris
  - **Demanda Diaria** ← NUEVA COLUMNA
    - "X u/día" (demanda promedio)
    - "X días cobertura"
  - Estado: Badge (Crítico/Bajo/Normal) con colores

- **Modal de Carga Excel**:
  - Drag & drop de archivo
  - Validación de formato (.xlsx, .xls)
  - Confirmación con advertencias
  - Barra de progreso animada
  - Resultado detallado (insertados/actualizados/errores)

**Cálculo de Estado**:
```javascript
const stockMinimo = producto.stock_minimo_dinamico || producto.stock_minimo;
const porcentaje = (producto.stock_actual / stockMinimo) * 100;

if (porcentaje < 50) return 'Crítico' (rojo);
if (porcentaje < 100) return 'Bajo' (amarillo);
return 'Normal' (verde);
```

**APIs Consumidas**:
- `GET /api/productos/?page=X&page_size=50&search=...&filtro_stock=...`
- `POST /api/productos/cargar_excel/`
- `GET /api/productos/ultima-carga/`

---

#### 4. Ofertas de Laboratorios (`/ofertas`)
**Archivo**: `src/pages/OfertasLaboratorio/OfertasLaboratorio.jsx`

**Funcionalidades**:
- **Header**:
  - Botón "Procesar Archivo" (cargar ofertas manuales)
  - Total de ofertas activas

- **Filtros**:
  - Búsqueda por producto
  - Selector de laboratorio (dropdown dinámico)
  - Checkbox "Solo ofertas activas"

- **Tabla Paginada** (50 por página):
  - Producto
  - Laboratorio
  - Precio Normal
  - Precio Oferta
  - % Descuento
  - Ahorro (CLP)
  - Vigencia (desde - hasta)
  - Estado (badge Activa/Vencida)

- **Modal de Carga**:
  - Soporta Excel y PDF
  - Progreso de procesamiento
  - Resumen de ofertas extraídas

**APIs Consumidas**:
- `GET /api/ofertas/por_laboratorio/?page=X&laboratorio=...&activas=true`
- `GET /api/ofertas/laboratorios/`
- `POST /api/ofertas/procesar/`

---

#### 5. Ventas (`/ventas`)
**Archivo**: `src/pages/Sales/Sales.jsx`

**Funcionalidades**:
- Formulario de registro de venta
- Búsqueda de cliente por RUT
- Búsqueda de productos
- Carrito de compra
- Cálculo de totales
- Métodos de pago: Efectivo, Tarjeta, Transferencia
- Tipo de documento: Boleta, Factura
- Historial de ventas (tabla paginada)

**APIs Consumidas**:
- `POST /api/ventas/`
- `GET /api/ventas/`
- `GET /api/clientes/?search=...`
- `GET /api/productos/?search=...`

---

#### 6. Predicción Estacional (`/prediccion-estacional`)
**Archivo**: `src/pages/SeasonalDemand/SeasonalDemand.jsx`

**Funcionalidades**:
- **Selector de Categoría**: Dropdown con 126 categorías farmacéuticas
- **Selector de Año**: 2026, 2027, 2028
- **Botón Actualizar**: Re-calcula predicción

- **KPIs** (4 cards):
  - Demanda Anual Proyectada (total transacciones)
  - Promedio Mensual
  - Mes de Mayor Demanda (destacado)
  - Categoría seleccionada + Año

- **Gráficos**:
  - Gráfico de líneas: Tendencia mensual
  - Gráfico de barras: Comparación mensual

- **Panel de Recomendaciones**:
  - Top 3 meses de mayor demanda
  - Acción sugerida por mes:
    - ⬆️ Aumentar stock significativamente (>130% promedio)
    - ↗️ Aumentar stock moderadamente (>110% promedio)
    - ✅ Mantener stock normal

**APIs Consumidas**:
- `GET /api/seasonal/categories/`
- `GET /api/seasonal/year/?categoria=X&año=Y`

**Ejemplo de Predicción**:
```javascript
{
  categoria: "ANTIGRIPAL",
  año: 2026,
  predicciones: [
    {mes: 1, mes_nombre: "Enero", prediccion: 231},
    {mes: 6, mes_nombre: "Junio", prediccion: 450},  // Invierno = alta demanda
    {mes: 12, mes_nombre: "Diciembre", prediccion: 235}
  ],
  total_anual_proyectado: 2805
}
```

---

#### 7. ETL Admin (`/etl`)
**Archivo**: `src/pages/ETL/ETL.jsx`

**Funcionalidades**:
- **Estado de Gmail**:
  - Badge: Conectado ✅ / Desconectado ❌
  - Botón "Conectar Gmail" (OAuth2 flow)
  - Botón "Revocar Acceso"

- **Ejecutar ETL Manual**:
  - Selector: "Días atrás" (1, 3, 5, 7)
  - Checkbox: "Modo estricto"
  - Botón "Ejecutar ETL"
  - Progreso en tiempo real (Server-Sent Events)

- **Diagnóstico**:
  - Test de conexión Gmail
  - Verificación de credenciales
  - Listado de remitentes configurados

- **Historial de Ejecuciones** (tabla):
  - Fecha/Hora
  - Emails procesados
  - Ofertas extraídas
  - Ofertas insertadas/actualizadas
  - Duración
  - Estado (Exitoso/Fallido)
  - Botón "Ver Detalles"

**APIs Consumidas**:
- `GET /api/gmail/auth/status/`
- `GET /api/gmail/auth/start/`
- `POST /api/etl/run/`
- `GET /api/etl/logs/`
- `GET /api/etl/progress/` (SSE)

---

#### 8. Sugerencias de Compra (`/sugerencias`)
**Archivo**: `src/pages/PurchaseSuggestions/PurchaseSuggestions.jsx`

**Funcionalidades**:
- Filtros por tipo de sugerencia:
  - Bajo Stock (crítico)
  - Predicción ML
  - Estacional

- Tabla de sugerencias:
  - Producto
  - Tipo de sugerencia
  - Cantidad sugerida
  - Prioridad (badge con color)
  - Razón detallada
  - Confianza ML (%)
  - Acciones (Procesar/Ignorar)

**APIs Consumidas**:
- `GET /api/sugerencias/`
- `POST /api/sugerencias/{id}/procesar/`

---

### Servicios API Frontend

**Archivo**: `src/services/api.js`

**Configuración Base**:
```javascript
const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {'Content-Type': 'application/json'},
});

// Interceptor para errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);
```

**Servicios Exportados**:
- `clientesService` - CRUD clientes + stats
- `transaccionesService` - CRUD transacciones
- `productosService` - CRUD productos + low-stock + top-selling + cargar Excel
- `dashboardService` - Stats + sales + top-products
- `sugerenciasService` - Sugerencias de compra
- `ofertasService` - CRUD ofertas + laboratorios
- `etlService` - ETL manual + logs + status
- `gmailAuthService` - OAuth Gmail
- `ventasService` - CRUD ventas + stats
- `authService` - Login con Google (futuro)

---

## 🔐 SEGURIDAD

### Backend

**Validaciones en Serializers** (`core/serializers.py`):
```python
# Ejemplo ProductoSerializer
def validate_codigo(self, value):
    # Solo alfanuméricos, guiones y guiones bajos
    if not re.match(r'^[a-zA-Z0-9\-_]+$', value.strip()):
        raise ValidationError("Caracteres no permitidos")
    return value.strip().upper()

def validate_nombre(self, value):
    # Prevenir XSS y SQL injection
    if not re.match(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\-\(\),\.]+$', value):
        raise ValidationError("Caracteres no permitidos")
    return value.strip()

def validate_stock_actual(self, value):
    if value < 0 or value > 1000000:
        raise ValidationError("Rango inválido")
    return value
```

**Sanitización de Datos**:
- RUT chileno: Normalización automática (sin puntos ni guiones)
- Emails: Validación con regex + unicidad
- Precios: Límite máximo 99,999,999.99
- Stocks: Límite máximo 1,000,000 unidades

**CORS** (`config/settings.py`):
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
]
```

**Deduplicación de Ventas**:
```python
# Hash único por venta para evitar duplicados
hash_data = f"{tipo_doc}:{numero}:{fecha}:{cliente.rut}:{total}"
hash_unico = hashlib.sha256(hash_data.encode()).hexdigest()

# Verificar antes de insertar
if Venta.objects.filter(hash_unico=hash_unico).exists():
    raise ValidationError("Venta duplicada")
```

### Gmail OAuth2

**Flujo de Autenticación**:
1. Usuario hace clic en "Conectar Gmail"
2. Backend genera URL de OAuth2 con Google
3. Frontend redirige a Google
4. Google autentica y redirige al callback
5. Backend intercambia código por token
6. Token se guarda en `credentials/gmail_token.json`

**Scopes Requeridos**:
- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/gmail.modify`

**Seguridad**:
- Client Secret en variable de entorno: `GMAIL_CLIENT_SECRET`
- Token refresh automático
- Revocación de acceso disponible

---

## 🚀 DESPLIEGUE Y CONFIGURACIÓN

### Variables de Entorno

**`.env` Principal**:
```bash
# Database
POSTGRES_DB=smartpharm_db
POSTGRES_USER=smartpharm_user
POSTGRES_PASSWORD=smartpharm_password_2024
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Django
SECRET_KEY=django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Gmail OAuth
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/gmail/auth/callback

# Frontend
REACT_APP_API_URL=http://localhost:8000

# ML Models
ML_MODELS_PATH=/app/ml_models
```

### Docker Compose

**Archivo**: `docker-compose.yml`

**Servicios**:
1. **db** (PostgreSQL 15)
   - Volumen: `postgres_data:/var/lib/postgresql/data`
   - Health check activo

2. **backend** (Django)
   - Build: `./Backend_Django`
   - Ports: 8000:8000
   - Depends on: db
   - Command: `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3`

3. **frontend** (React + Nginx)
   - Build: `./Frontend_React`
   - Multi-stage: Node build → Nginx serve
   - Ports: 3000:80

4. **redis** (Broker para Celery)
   - Image: redis:alpine
   - Ports: 6379:6379

5. **celery_worker**
   - Build: `./Backend_Django`
   - Command: `celery -A config worker -l info`
   - Depends on: db, redis

6. **celery_beat** (Scheduler)
   - Command: `celery -A config beat -l info`

### Comandos de Gestión

**Iniciar Sistema**:
```bash
docker-compose up -d
```

**Rebuild Frontend** (después de cambios):
```bash
docker-compose up -d --build frontend
```

**Ver Logs**:
```bash
docker logs smartpharm_backend -f
docker logs smartpharm_frontend -f
```

**Ejecutar Migraciones**:
```bash
docker exec smartpharm_backend python manage.py migrate
```

**Crear Superusuario**:
```bash
docker exec -it smartpharm_backend python manage.py createsuperuser
```

**Cargar Datos de Prueba**:
```bash
docker exec smartpharm_backend python manage.py seed_data
```

**Ejecutar ETL Manual**:
```bash
docker exec smartpharm_backend python manage.py run_etl --days-back 5
```

**Shell Django**:
```bash
docker exec -it smartpharm_backend python manage.py shell
```

**PostgreSQL Shell**:
```bash
docker exec -it smartpharm_db psql -U smartpharm_user -d smartpharm_db
```

---

## 📊 DATOS ACTUALES DEL SISTEMA

### Estadísticas Reales (Noviembre 2025)

**Clientes**:
- Total: 2,848 clientes
- Frecuentes (≥5 compras): 2,683 (94.2%)
- Normales (<5 compras): 165 (5.8%)
- Elegibles para ofertas: 2,683

**Ventas**:
- Total acumulado: $808,153,801 CLP
- Ventas mes reciente (Sept 2025): $14,054,047 CLP
- Total transacciones: 114,955 ventas
- Período de datos: Septiembre 2025

**Inventario**:
- Total productos: 4,700
- Productos activos: 4,700
- Última carga: Variable según Excel cargado

**Productos Más Vendidos**:
1. GENIOL SOBRE LIMONADA - 14,919 unidades
2. [Top 10 disponible en dashboard]

**Modelo ML**:
- Categorías farmacéuticas: 126
- Productos con categoría válida: Pendiente de categorización
- Actualmente usando: Categoría "General" (fallback)

---

## 🔧 FUNCIONALIDADES AVANZADAS

### 1. Sistema de Paginación Inteligente

**Backend** - Clase base:
```python
# core/main_views.py
class OfertasPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200
```

**Frontend** - Componente reutilizable:
```javascript
// Controles de paginación con:
- Primera página
- Página anterior
- Indicador: "Página X de Y"
- Página siguiente
- Última página
- Info: "Mostrando 1 a 50 de 2848 resultados"
```

### 2. Búsqueda con Debounce

**Implementación**:
```javascript
const [searchInput, setSearchInput] = useState('');
const [searchTerm, setSearchTerm] = useState('');

useEffect(() => {
  const timer = setTimeout(() => {
    setSearchTerm(searchInput);
    setCurrentPage(1);
  }, 500); // Espera 500ms después de dejar de escribir

  return () => clearTimeout(timer);
}, [searchInput]);
```

**Beneficio**: Reduce llamadas API innecesarias mientras el usuario escribe.

### 3. Auto-Refresh en Dashboard

```javascript
useEffect(() => {
  cargarDatos();
  const interval = setInterval(cargarDatos, 30000); // 30 segundos
  return () => clearInterval(interval);
}, []);
```

### 4. Carga de Excel con Validación

**Validaciones Frontend**:
- Extensión: Solo .xlsx, .xls
- Tamaño máximo: Configurable
- Confirmación obligatoria antes de cargar

**Validaciones Backend**:
- Detección automática de fila de headers (primeras 20 filas)
- Normalización de nombres de columnas
- Validación de tipos de datos
- Manejo de errores por fila
- Deduplicación por código

**Resultado Detallado**:
```json
{
  "message": "Inventario cargado exitosamente",
  "productos_insertados": 420,
  "productos_actualizados": 80,
  "errores": [
    "Fila 15: Precio inválido",
    "Fila 23: Código duplicado"
  ]
}
```

### 5. Server-Sent Events (SSE) para ETL

**Backend**:
```python
@api_view(['GET'])
def get_etl_progress(request):
    def event_stream():
        while task_running:
            progress = get_current_progress()
            yield f"data: {json.dumps(progress)}\n\n"
            time.sleep(1)

    return StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
```

**Frontend**:
```javascript
const eventSource = new EventSource('/api/etl/progress/');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  setProgress(data.progress);
  setStatus(data.status);
};
```

### 6. Mapeo Automático Producto-Proveedor

**Estrategia**:
```python
# Intentar match exacto por código
mapping = ProductoProveedorMapping.objects.filter(
    codigo_proveedor=codigo_oferta,
    proveedor=laboratorio
).first()

# Si no existe, buscar por similitud de nombre (Levenshtein)
if not mapping:
    productos = Producto.objects.all()
    best_match = max(productos, key=lambda p:
        fuzz.ratio(p.nombre, nombre_oferta)
    )

    if similarity > 80:
        create_automatic_mapping(
            producto=best_match,
            codigo_proveedor=codigo_oferta,
            confianza=similarity
        )
```

### 7. Gestión de Errores Unificada

**Frontend**:
```javascript
try {
  const response = await api.get('/endpoint/');
  setData(response.data);
} catch (error) {
  const message = error.response?.data?.message
    || error.message
    || 'Error desconocido';
  setError(message);
}
```

**Backend**:
```python
try:
    # Operación
except ValidationError as e:
    return Response({'error': str(e)}, status=400)
except Exception as e:
    logger.error(f"Error: {str(e)}")
    return Response({'error': 'Error interno'}, status=500)
```

---

## 📈 CASOS DE USO PRINCIPALES

### Caso 1: Análisis de Clientes Frecuentes

**Flujo**:
1. Usuario accede a `/clientes`
2. Sistema carga estadísticas globales (API `/clientes/stats/`)
3. Usuario filtra "Clientes frecuentes"
4. Sistema muestra solo clientes con ≥5 compras
5. Usuario hace clic en "Enviar Ofertas a Clientes Frecuentes"
6. Sistema prepara campaña de email marketing para 2,683 clientes

**Beneficio**: Identificar y retener clientes de alto valor.

---

### Caso 2: Gestión de Stock con Predicción ML

**Flujo**:
1. Usuario accede a `/inventario`
2. Sistema calcula stock mínimo dinámico para cada producto
3. Para productos con categoría válida:
   - Consulta modelo ML para predicción del próximo mes
   - Ajusta stock mínimo según estacionalidad
4. Usuario ve:
   - Stock Mín. (Dinámico): 15 unidades (en azul)
   - (fijo: 10) en gris si difiere
   - Demanda: 2.3 u/día, 45 días cobertura
5. Sistema marca productos con stock crítico (<50% del dinámico)

**Beneficio**: Optimizar niveles de inventario según demanda real predicha.

---

### Caso 3: Procesamiento Automático de Ofertas

**Flujo**:
1. Laboratorio envía email con Excel de ofertas a correo configurado
2. Celery Beat ejecuta tarea ETL cada mañana (6:00 AM)
3. ETL:
   - Consulta Gmail API (últimos 5 días)
   - Descarga adjunto Excel de Mediven
   - Parsea: 450 ofertas encontradas
   - Normaliza datos y valida precios
   - Inserta 420 nuevas ofertas, actualiza 30 existentes
4. Usuario accede a `/ofertas` y ve ofertas actualizadas
5. Usuario filtra por "Mediven" y encuentra producto en oferta

**Beneficio**: Automatizar captura de ofertas sin intervención manual.

---

### Caso 4: Predicción de Demanda Estacional

**Flujo**:
1. Usuario accede a `/prediccion-estacional`
2. Selecciona "ANTIGRIPAL" y año "2026"
3. Sistema:
   - Carga modelo ML Random Forest
   - Analiza ventas históricas de antigripes
   - Calcula features (lags, promedios móviles)
   - Predice 12 meses del 2026
4. Sistema muestra:
   - Junio 2026: 450 transacciones (ALTA demanda, invierno)
   - Enero 2026: 231 transacciones (normal, verano)
5. Recomendación: "⬆️ Aumentar stock significativamente para Junio"

**Beneficio**: Anticipar picos estacionales y ajustar compras.

---

### Caso 5: Carga Masiva de Inventario

**Flujo**:
1. Usuario recibe Excel actualizado del proveedor con 5,000 productos
2. Usuario accede a `/inventario` → "Cargar Excel"
3. Selecciona archivo, sistema muestra confirmación con advertencias
4. Usuario confirma, sistema:
   - Valida formato
   - Detecta headers automáticamente (fila 3)
   - Normaliza códigos y precios
   - Procesa barra de progreso (0% → 100%)
5. Resultado:
   - 4,700 productos actualizados
   - 300 productos nuevos insertados
   - 0 errores
6. Timestamp "Última actualización" se actualiza

**Beneficio**: Sincronizar inventario rápidamente sin carga manual.

---

## 🐛 DEBUGGING Y TROUBLESHOOTING

### Comandos Útiles

**Ver logs en tiempo real**:
```bash
docker logs smartpharm_backend -f --tail 100
```

**Verificar estado de contenedores**:
```bash
docker ps
docker-compose ps
```

**Reiniciar servicios**:
```bash
docker-compose restart backend
docker-compose restart frontend
docker-compose restart celery_worker
```

**Verificar conectividad API**:
```bash
curl http://localhost:8000/api/clientes/stats/ | python -m json.tool
```

**Shell interactivo Django**:
```bash
docker exec -it smartpharm_backend python manage.py shell

# Dentro del shell:
from core.models import Cliente, Producto, Venta
print(Cliente.objects.count())
print(Producto.objects.filter(bajo_stock=True).count())
```

**Inspeccionar base de datos**:
```bash
docker exec -it smartpharm_db psql -U smartpharm_user -d smartpharm_db

# SQL:
SELECT COUNT(*) FROM core_cliente;
SELECT * FROM core_etllog ORDER BY fecha_ejecucion DESC LIMIT 5;
```

---

## 🔮 ROADMAP Y MEJORAS FUTURAS

### En Desarrollo
- [ ] Autenticación con Google OAuth (frontend)
- [ ] Roles y permisos (Admin, Vendedor, Gerente)
- [ ] Exportación de reportes (Excel, PDF)
- [ ] Notificaciones push para stock crítico
- [ ] Chatbot de consultas con IA

### Planeado
- [ ] App móvil (React Native)
- [ ] Integración con POS (punto de venta)
- [ ] Facturación electrónica (SII Chile)
- [ ] Dashboard ejecutivo con Power BI
- [ ] Predicción de rotación de productos (churn)

### Optimizaciones
- [ ] Cache Redis para consultas frecuentes
- [ ] Índices adicionales en BD para búsquedas
- [ ] Lazy loading de imágenes de productos
- [ ] Compresión de archivos estáticos
- [ ] CDN para assets frontend

---

## 📚 REFERENCIAS Y TECNOLOGÍAS

### Backend
- Django 4.2 - https://www.djangoproject.com/
- Django REST Framework 3.14 - https://www.django-rest-framework.org/
- Celery 5.3 - https://docs.celeryq.dev/
- PostgreSQL 15 - https://www.postgresql.org/
- scikit-learn 1.3 (Random Forest) - https://scikit-learn.org/
- PyPDF2 / pdfplumber - Parsing de PDFs
- openpyxl / xlrd - Lectura de Excel
- Google APIs Client - Gmail integration

### Frontend
- React 18 - https://react.dev/
- Vite 5 - https://vitejs.dev/
- TailwindCSS 3 - https://tailwindcss.com/
- Recharts 2.5 - https://recharts.org/
- Axios 1.6 - https://axios-http.com/
- Lucide React - https://lucide.dev/

### DevOps
- Docker 24 - https://www.docker.com/
- Docker Compose 2 - https://docs.docker.com/compose/
- Nginx (Alpine) - https://nginx.org/
- Gunicorn 23 - https://gunicorn.org/

---

## 📞 CONTACTO Y SOPORTE

**Proyecto**: SmartPharm CRM v2.0
**Tipo**: Sistema de Gestión para Farmacias
**Entorno**: Desarrollo (Docker local)
**Puerto Frontend**: http://localhost:3000
**Puerto Backend**: http://localhost:8000
**Admin Django**: http://localhost:8000/admin/

---

**Fecha de Documento**: Noviembre 2025
**Versión**: 2.0.0

---

## APÉNDICE: ESTRUCTURA DE DIRECTORIOS

```
sistema_aplicacion_V2/
├── Backend_Django/
│   ├── config/               # Configuración Django
│   │   ├── settings.py      # Settings principal
│   │   ├── urls.py          # URLs globales
│   │   ├── wsgi.py          # WSGI application
│   │   └── celery.py        # Configuración Celery
│   ├── core/                # App principal
│   │   ├── models.py        # Modelos de BD (15 modelos)
│   │   ├── serializers.py   # Serializers DRF
│   │   ├── main_views.py    # ViewSets principales
│   │   ├── seasonal_views.py # Vistas predicción ML
│   │   ├── ml_service.py    # Servicio ML
│   │   ├── stock_service.py # Servicio stock dinámico
│   │   ├── admin.py         # Django Admin config
│   │   ├── etl/
│   │   │   └── offer_etl.py # Lógica ETL
│   │   ├── parsers/
│   │   │   ├── excel_parser.py
│   │   │   └── pdf_parser.py
│   │   └── management/
│   │       └── commands/
│   │           ├── run_etl.py
│   │           ├── seed_data.py
│   │           └── import_farmacia.py
│   ├── ml_models/           # Modelos ML entrenados
│   │   ├── modelo_prediccion_estacional.pkl
│   │   └── label_encoder_categorias.pkl
│   ├── requirements.txt     # Dependencias Python
│   └── Dockerfile
├── Frontend_React/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard/
│   │   │   ├── Customers/
│   │   │   ├── Inventory/
│   │   │   ├── OfertasLaboratorio/
│   │   │   ├── Sales/
│   │   │   ├── SeasonalDemand/
│   │   │   ├── ETL/
│   │   │   └── PurchaseSuggestions/
│   │   ├── services/
│   │   │   └── api.js       # Servicios API
│   │   ├── App.jsx          # Componente raíz
│   │   └── main.jsx         # Entry point
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml       # Orquestación contenedores
├── .env                     # Variables de entorno
└── README.md
```

---

## FIN DEL DOCUMENTO
