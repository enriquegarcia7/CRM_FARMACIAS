# Formato Excel para Carga de Ventas

Este documento describe el formato del archivo Excel requerido para cargar transacciones de ventas en el sistema.

## Columnas Requeridas

El archivo Excel debe contener las siguientes columnas (el orden no importa, pero los nombres deben coincidir):

| Columna | Descripción | Tipo | Ejemplo | Requerido |
|---------|-------------|------|---------|-----------|
| **TIPO DOCUMENTO** | Tipo de documento de venta | Texto | Factura, Boleta, Nota de Crédito | Opcional |
| **NUMERO DOCUMENTO** | Número único del documento | Texto/Número | 123456, F-001-00123 | Opcional |
| **FECHA** | Fecha de la transacción | Fecha | 01/01/2024, 2024-01-01 | **Requerido** |
| **NOMBRE CLIENTE** | Nombre completo del cliente | Texto | Juan Pérez | Opcional |
| **CORREO** | Correo electrónico del cliente | Email | juan.perez@email.com | Opcional |
| **CODIGO** | Código del producto | Texto | MED001, PARA-500 | **Requerido** |
| **PRODUCTO** | Nombre/descripción del producto | Texto | Paracetamol 500mg | **Requerido** |
| **CANTIDAD** | Cantidad vendida | Número | 2, 10 | **Requerido** |
| **PRECIO** | Precio unitario | Número | 3000, 4500.50 | **Requerido** |
| **CLIENTE_ID** | Identificador único del cliente (RUT) | Texto | 12345678-9 | **Requerido** |

## Columnas Opcionales Adicionales

Si el Excel contiene estas columnas, también serán procesadas:

- **DESCUENTO**: Descuento aplicado
- **NETO**: Monto neto de la línea
- **FECHA VENCIMIENTO**: Fecha de vencimiento del documento
- **ORDEN COMPRA**: Número de orden de compra
- **VENDEDOR**: Nombre del vendedor
- **DISTRIBUIDOR**: Distribuidor asociado
- **SUCURSAL**: Sucursal de origen
- **CENTRO COSTO**: Centro de costo
- **CUENTA**: Cuenta contable
- **FAMILIA**: Familia o categoría del producto

## Nombres Alternativos

El sistema reconoce variaciones en los nombres de columnas:

| Columna Estándar | Variaciones Aceptadas |
|-----------------|----------------------|
| CLIENTE_ID | CLIENTE ID, ID CLIENTE, RUT, CLIENTE RUT |
| NOMBRE CLIENTE | NOMBRE_CLIENTE, NOMBRE, CLIENTE |
| CORREO | EMAIL, E-MAIL, CORREO ELECTRONICO |
| NUMERO DOCUMENTO | NÚMERO DOCUMENTO, NUMERO, NRO, N° |
| CODIGO | CÓDIGO, COD, SKU |
| PRECIO | PRECIO UNITARIO, PRECIO_UNITARIO |

## Formato de Datos

### Fechas
- **Formatos aceptados**: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, DD/MM/YY
- **Ejemplos**: 31/12/2024, 2024-12-31, 31-12-24

### Precios
- **Formato chileno**: 1.234,56 (punto para miles, coma para decimal)
- **Formato internacional**: 1234.56 (punto para decimal)
- **Con símbolo**: $1.234,56
- El sistema detecta automáticamente el formato

### RUT (CLIENTE_ID)
- **Con formato**: 12.345.678-9
- **Sin formato**: 12345678-9
- El sistema normaliza automáticamente

## Ejemplo de Excel

```
TIPO DOCUMENTO | NUMERO DOCUMENTO | FECHA      | NOMBRE CLIENTE | CORREO              | CODIGO  | PRODUCTO           | CANTIDAD | PRECIO | CLIENTE_ID
---------------|------------------|------------|----------------|---------------------|---------|--------------------|---------:|-------:|-----------
Factura        | F-001-00123      | 01/01/2024 | Juan Pérez     | juan@email.com      | MED001  | Paracetamol 500mg  |        2 |   3000 | 12345678-9
Boleta         | B-002-00456      | 02/01/2024 | María Silva    | maria@email.com     | MED002  | Ibuprofeno 400mg   |        1 |   4500 | 98765432-1
Factura        | F-001-00124      | 03/01/2024 | Pedro González | pedro@email.com     | MED003  | Amoxicilina 500mg  |        3 |   8000 | 11111111-1
```

## Comportamiento del Sistema

### Clientes
- Si el CLIENTE_ID (RUT) ya existe en el sistema:
  - Se actualiza el nombre y correo si se proporcionan en el Excel
  - Solo se actualiza el nombre si el actual es genérico ("Cliente 12345678-9")
- Si el CLIENTE_ID no existe:
  - Se crea un nuevo cliente con los datos proporcionados
  - Si no se proporciona nombre, se usa "Cliente {RUT}"

### Productos
- El CODIGO debe existir en el inventario de productos
- Si el producto no existe, la línea se salta y se reporta en los errores
- Se recomienda sincronizar productos antes de cargar ventas

### Ventas Duplicadas
- El sistema detecta ventas duplicadas usando un hash único
- Hash = MD5(NUMERO_DOCUMENTO + CLIENTE_ID + FECHA)
- Las ventas duplicadas se omiten automáticamente

### Agrupación
- Las líneas con el mismo NUMERO_DOCUMENTO, CLIENTE_ID y FECHA se agrupan en una sola venta
- Cada línea se convierte en un detalle de venta (DetalleVenta)

## Uso para Análisis Predictivo

Este formato está optimizado para análisis predictivo de demanda estacional:

### Datos Clave para Predicción
1. **FECHA**: Permite análisis temporal y detección de estacionalidad
2. **CODIGO + PRODUCTO**: Identifica productos para análisis individual
3. **CANTIDAD**: Métrica principal para predicción de demanda
4. **PRECIO**: Permite analizar elasticidad precio-demanda
5. **CLIENTE_ID**: Permite segmentación y análisis por cliente

### Análisis Posibles
- **Demanda estacional**: Patrones por mes, trimestre, temporada
- **Tendencias**: Crecimiento/decrecimiento de productos
- **Productos complementarios**: Análisis de co-compra
- **Segmentación de clientes**: Patrones de compra por tipo de cliente
- **Predicción de stock**: Basada en histórico de ventas

## Validaciones

El sistema valida:
- ✅ Fechas en formato válido
- ✅ CLIENTE_ID no vacío
- ✅ CODIGO existe en el inventario
- ✅ CANTIDAD > 0
- ✅ PRECIO > 0 (o se calcula desde NETO)

## Respuesta de Carga

Al cargar el archivo, el sistema retorna:
```json
{
  "message": "Archivo de ventas procesado correctamente",
  "ventas_insertadas": 150,
  "ventas_duplicadas": 5,
  "detalles_insertados": 420,
  "clientes_creados": 12,
  "productos_no_encontrados": 3,
  "errores": [
    "Fila 45: Producto ABC123 no encontrado en inventario",
    "Fila 67: Fecha inválida"
  ]
}
```

## Endpoint de Carga

**URL**: `POST /api/ventas/cargar_excel/`

**Headers**:
```
Content-Type: multipart/form-data
```

**Body**:
```
archivo: [archivo.xlsx]
```

## Notas Importantes

1. **Primera vez**: Asegúrate de que los productos estén cargados en el inventario antes de cargar ventas
2. **Encoding**: Usar UTF-8 para caracteres especiales (ñ, á, etc.)
3. **Tamaño**: Se recomienda cargar archivos de máximo 10,000 filas por lote
4. **Rendimiento**: La carga es transaccional; si hay un error crítico, se hace rollback completo
5. **Logs**: Todos los errores y advertencias se registran en el log del sistema
