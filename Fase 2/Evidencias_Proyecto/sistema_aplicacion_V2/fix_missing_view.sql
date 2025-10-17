-- Crear la vista materializada de segmentación que faltó

-- Primero verificar si ya existe y eliminarla si es necesario
DROP MATERIALIZED VIEW IF EXISTS mv_segmentacion_clientes CASCADE;

-- Crear la vista materializada
CREATE MATERIALIZED VIEW mv_segmentacion_clientes AS
WITH compras_detalle AS (
    SELECT
        b.rut_cliente,
        c.nombre as nombre_cliente,
        p.codigo_producto,
        p.principio_activo,
        p.categoria,
        cm.tipo_uso,
        b.fecha_emision,
        dv.cantidad,
        dv.subtotal,
        LAG(b.fecha_emision) OVER (PARTITION BY b.rut_cliente, p.codigo_producto ORDER BY b.fecha_emision) as fecha_anterior
    FROM boletas b
    INNER JOIN detalle_ventas dv ON b.numero_boleta = dv.numero_boleta
    INNER JOIN productos p ON dv.codigo_producto = p.codigo_producto
    INNER JOIN clientes c ON b.rut_cliente = c.rut
    LEFT JOIN clasificacion_medicamentos cm ON p.principio_activo = cm.principio_activo
    WHERE p.principio_activo IS NOT NULL AND p.principio_activo != ''
),
cliente_medicamentos AS (
    SELECT
        rut_cliente,
        nombre_cliente,
        principio_activo,
        categoria,
        tipo_uso,
        COUNT(DISTINCT fecha_emision) as total_compras,
        SUM(cantidad) as cantidad_total,
        MIN(fecha_emision) as primera_compra,
        MAX(fecha_emision) as ultima_compra,
        SUM(subtotal) as gasto_total,
        ROUND(AVG(CASE
            WHEN fecha_anterior IS NOT NULL
            THEN EXTRACT(EPOCH FROM (fecha_emision::timestamp - fecha_anterior::timestamp))/86400
            ELSE NULL
        END)) as dias_promedio_entre_compras
    FROM compras_detalle
    GROUP BY rut_cliente, nombre_cliente, principio_activo, categoria, tipo_uso
),
clasificacion AS (
    SELECT
        rut_cliente,
        nombre_cliente,
        principio_activo,
        categoria,
        tipo_uso,
        total_compras,
        cantidad_total,
        primera_compra,
        ultima_compra,
        CURRENT_DATE - ultima_compra as dias_sin_compra,
        gasto_total,
        dias_promedio_entre_compras,
        CASE
            WHEN tipo_uso = 'CRONICO' AND total_compras >= 3 THEN 'CLIENTE_CRONICO'
            WHEN tipo_uso = 'ESTACIONAL' AND total_compras >= 2 THEN 'CLIENTE_ESTACIONAL'
            WHEN tipo_uso = 'AGUDO' AND total_compras >= 5 THEN 'CLIENTE_RECURRENTE_AGUDO'
            WHEN gasto_total >= 50000 THEN 'CLIENTE_ALTO_VALOR'
            ELSE 'CLIENTE_OCASIONAL'
        END as segmento_cliente
    FROM cliente_medicamentos
)
SELECT * FROM clasificacion;

-- Crear índices para la vista materializada
CREATE UNIQUE INDEX idx_mv_seg_cliente_producto ON mv_segmentacion_clientes(rut_cliente, principio_activo);
CREATE INDEX idx_mv_seg_segmento ON mv_segmentacion_clientes(segmento_cliente);
CREATE INDEX idx_mv_seg_tipo_uso ON mv_segmentacion_clientes(tipo_uso);
CREATE INDEX idx_mv_seg_dias_sin_compra ON mv_segmentacion_clientes(dias_sin_compra DESC);

COMMENT ON MATERIALIZED VIEW mv_segmentacion_clientes IS 'Segmentación de clientes por tipo de medicamento y patrón de compra';
