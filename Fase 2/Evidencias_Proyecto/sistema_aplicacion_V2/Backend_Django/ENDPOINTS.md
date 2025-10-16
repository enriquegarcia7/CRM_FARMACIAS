# SmartPharm API Endpoints

## Base URL
```
http://localhost:8000/api/
```

## Endpoints Implementados

### 1. Clientes
- `GET /api/clientes/` - Lista todos los clientes
- `POST /api/clientes/` - Crear nuevo cliente
- `GET /api/clientes/{id}/` - Obtener un cliente específico
- `PUT /api/clientes/{id}/` - Actualizar cliente
- `DELETE /api/clientes/{id}/` - Eliminar cliente
- `GET /api/clientes/frecuentes/` - Obtener clientes frecuentes (≥5 compras)

**Respuesta de ejemplo:**
```json
{
  "id": 1,
  "nombre": "María González",
  "correo": "maria@email.com",
  "telefono": "+56912345678",
  "fecha_registro": "2025-01-15T10:30:00Z",
  "total_compras": 8,
  "monto_total": 1200000,
  "ultima_compra": "2025-10-12",
  "frecuencia": "frecuente"
}
```

### 2. Productos
- `GET /api/productos/` - Lista todos los productos
- `POST /api/productos/` - Crear nuevo producto
- `GET /api/productos/{id}/` - Obtener un producto específico
- `PUT /api/productos/{id}/` - Actualizar producto
- `DELETE /api/productos/{id}/` - Eliminar producto
- `GET /api/productos/low_stock/` - Productos con bajo stock
- `GET /api/productos/top_selling/?limit=10` - Top productos más vendidos

**Respuesta de ejemplo:**
```json
{
  "id": 1,
  "codigo": "MED-001",
  "descripcion": "Paracetamol 500mg",
  "categoria": "Analgésico",
  "stock_actual": 850,
  "stock_minimo": 200,
  "precio_venta": 5000,
  "precio_costo": 3000,
  "activo": true,
  "bajo_stock": false
}
```

### 3. Proveedores
- `GET /api/proveedores/` - Lista todos los proveedores
- `POST /api/proveedores/` - Crear nuevo proveedor
- `GET /api/proveedores/{id}/` - Obtener un proveedor específico
- `PUT /api/proveedores/{id}/` - Actualizar proveedor
- `DELETE /api/proveedores/{id}/` - Eliminar proveedor

### 4. Ofertas de Laboratorios
- `GET /api/ofertas/` - Lista todas las ofertas activas
- `POST /api/ofertas/` - Crear nueva oferta
- `GET /api/ofertas/{id}/` - Obtener una oferta específica
- `PUT /api/ofertas/{id}/` - Actualizar oferta
- `DELETE /api/ofertas/{id}/` - Eliminar oferta
- `POST /api/ofertas/procesar/` - Procesar archivo de ofertas (Excel/PDF)

**Procesar archivo:**
```bash
curl -X POST http://localhost:8000/api/ofertas/procesar/ \
  -H "Content-Type: multipart/form-data" \
  -F "archivo=@ofertas.xlsx"
```

### 5. Sugerencias de Compra
- `GET /api/sugerencias/` - Lista todas las sugerencias no procesadas
- `POST /api/sugerencias/` - Crear nueva sugerencia
- `GET /api/sugerencias/{id}/` - Obtener una sugerencia específica
- `PUT /api/sugerencias/{id}/` - Actualizar sugerencia
- `DELETE /api/sugerencias/{id}/` - Eliminar sugerencia
- `GET /api/sugerencias/low_stock/` - Sugerencias por bajo stock
- `GET /api/sugerencias/season/` - Sugerencias estacionales (ML)
- `GET /api/sugerencias/epidemiological/` - Sugerencias epidemiológicas (MINSAL)

**Respuesta de ejemplo:**
```json
{
  "id": 1,
  "producto": 1,
  "producto_codigo": "MED-003",
  "producto_descripcion": "Amoxicilina 500mg",
  "producto_stock": 45,
  "producto_minimo": 100,
  "tipo": "bajo_stock",
  "cantidad_sugerida": 200,
  "prioridad": "alta",
  "razon": "Stock crítico - reposición urgente",
  "confianza_ml": null,
  "fuente_datos": "",
  "procesada": false
}
```

### 6. Ventas
- `GET /api/ventas/` - Lista todas las ventas
- `POST /api/ventas/` - Crear nueva venta
- `GET /api/ventas/{id}/` - Obtener una venta específica
- `PUT /api/ventas/{id}/` - Actualizar venta
- `DELETE /api/ventas/{id}/` - Eliminar venta

**Respuesta de ejemplo:**
```json
{
  "id": 1,
  "cliente": 1,
  "cliente_nombre": "María González",
  "fecha": "2025-10-14T15:30:00Z",
  "total": 125000,
  "metodo_pago": "tarjeta",
  "estado": "completada",
  "detalles": [
    {
      "id": 1,
      "producto": 1,
      "producto_descripcion": "Paracetamol 500mg",
      "cantidad": 10,
      "precio_unitario": 5000,
      "subtotal": 50000
    }
  ]
}
```

### 7. Dashboard (Estadísticas)
- `GET /api/dashboard/stats/` - Estadísticas generales del dashboard
- `GET /api/dashboard/sales/` - Datos de ventas para gráficos
- `GET /api/dashboard/top_products/?limit=10` - Top productos más vendidos

**Respuesta de stats:**
```json
{
  "total_ventas": 45780000,
  "ventas_mes": 8950000,
  "productos_stock": 342,
  "clientes_activos": 128
}
```

**Respuesta de sales:**
```json
[
  {"mes": "2025-01", "total": 6500000},
  {"mes": "2025-02", "total": 7200000},
  {"mes": "2025-03", "total": 6800000}
]
```

**Respuesta de top_products:**
```json
[
  {
    "producto__codigo": "MED-001",
    "producto__descripcion": "Paracetamol 500mg",
    "cantidad": 850,
    "ventas": 2550000
  }
]
```

### 8. Transacciones (Legado)
- `GET /api/transacciones/` - Lista todas las transacciones
- `POST /api/transacciones/` - Crear nueva transacción
- `GET /api/transacciones/{id}/` - Obtener una transacción específica
- `PUT /api/transacciones/{id}/` - Actualizar transacción
- `DELETE /api/transacciones/{id}/` - Eliminar transacción
- `GET /api/transacciones/stats/` - Estadísticas de transacciones

## Códigos de Estado HTTP

- `200 OK` - Solicitud exitosa
- `201 Created` - Recurso creado exitosamente
- `204 No Content` - Recurso eliminado exitosamente
- `400 Bad Request` - Error en los datos enviados
- `404 Not Found` - Recurso no encontrado
- `500 Internal Server Error` - Error del servidor

## Autenticación

Actualmente los endpoints no requieren autenticación. Para producción se recomienda implementar:
- Token Authentication (DRF)
- JWT (JSON Web Tokens)
- OAuth2

## CORS

El backend está configurado para aceptar peticiones desde:
- `http://localhost:5173` (React dev server)
- `http://127.0.0.1:5173`

## Ejemplos de Uso

### Usando curl

```bash
# Obtener todos los productos
curl http://localhost:8000/api/productos/

# Crear un nuevo cliente
curl -X POST http://localhost:8000/api/clientes/ \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Pérez",
    "correo": "juan@email.com",
    "telefono": "+56987654321"
  }'

# Obtener clientes frecuentes
curl http://localhost:8000/api/clientes/frecuentes/

# Obtener estadísticas del dashboard
curl http://localhost:8000/api/dashboard/stats/
```

### Usando Axios (React)

```javascript
import axios from 'axios';

// Obtener productos
const productos = await axios.get('http://localhost:8000/api/productos/');

// Crear venta
const venta = await axios.post('http://localhost:8000/api/ventas/', {
  cliente: 1,
  total: 50000,
  metodo_pago: 'tarjeta',
  estado: 'completada'
});

// Obtener sugerencias por bajo stock
const sugerencias = await axios.get('http://localhost:8000/api/sugerencias/low_stock/');
```

## Notas Importantes

1. **Datos de Prueba:** Actualmente la base de datos está vacía. Necesitas poblarla con datos de prueba o usar el admin de Django.

2. **Migraciones:** Ya aplicadas. Los modelos están creados en la base de datos.

3. **Admin Panel:** Accede a `http://localhost:8000/admin/` para gestionar datos manualmente.

4. **Frontend:** El frontend React espera estos endpoints y está configurado para consumirlos automáticamente.

## Próximos Pasos

- Crear datos de prueba (fixtures)
- Implementar autenticación
- Agregar paginación a los listados
- Implementar filtros avanzados
- Agregar validaciones personalizadas
- Implementar ML, ETL y sistema de emails (ver ROADMAP.md)
