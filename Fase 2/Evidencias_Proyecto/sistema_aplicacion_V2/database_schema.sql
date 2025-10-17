-- ============================================================================
-- SMARTPHARM CRM - ESQUEMA DE BASE DE DATOS
-- ============================================================================

-- NOTA: La base de datos smartpharm_db ya existe en Docker
-- Este script crea las tablas y estructuras necesarias

-- EXTENSIONES NECESARIAS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Para búsquedas de texto similares

-- ============================================================================
-- 1. TABLA: CLIENTES
-- Almacena información de clientes de la farmacia
-- ============================================================================
CREATE TABLE clientes (
    rut VARCHAR(12) PRIMARY KEY,  -- Formato: 12345678-9
    nombre VARCHAR(200) NOT NULL,
    email VARCHAR(150),
    telefono VARCHAR(15),
    fecha_registro DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_nacimiento DATE,
    es_frecuente BOOLEAN DEFAULT FALSE, -- Flag para clientes frecuentes
    descuento_porcentaje DECIMAL(5,2) DEFAULT 0.00, -- Descuento aplicable
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_rut_formato CHECK (rut ~ '^\d{7,8}-[\dKk]$'),
    CONSTRAINT chk_email_formato CHECK (email IS NULL OR email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'),
    CONSTRAINT chk_descuento CHECK (descuento_porcentaje >= 0 AND descuento_porcentaje <= 100)
);

-- Índices para clientes
CREATE INDEX idx_clientes_nombre ON clientes USING gin(nombre gin_trgm_ops);
CREATE INDEX idx_clientes_frecuente ON clientes(es_frecuente) WHERE es_frecuente = TRUE;
CREATE INDEX idx_clientes_activo ON clientes(activo) WHERE activo = TRUE;

COMMENT ON TABLE clientes IS 'Información de clientes de la farmacia (20,000 registros)';
COMMENT ON COLUMN clientes.es_frecuente IS 'Cliente con ≥10 compras o compras recurrentes de medicamentos crónicos';
COMMENT ON COLUMN clientes.descuento_porcentaje IS 'Porcentaje de descuento para clientes frecuentes (0-100)';

-- ============================================================================
-- 2. TABLA: CLASIFICACION_MEDICAMENTOS
-- Tabla maestra para clasificación de principios activos y categorías
-- ============================================================================
CREATE TABLE clasificacion_medicamentos (
    id SERIAL PRIMARY KEY,
    principio_activo VARCHAR(300) UNIQUE NOT NULL,
    categoria VARCHAR(150) NOT NULL,
    tipo_uso VARCHAR(20) NOT NULL, -- CRONICO, AGUDO, ESTACIONAL, PREVENTIVO
    es_estacional BOOLEAN DEFAULT FALSE,
    estacion_pico VARCHAR(20), -- INVIERNO, PRIMAVERA, VERANO, OTOÑO
    descripcion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_tipo_uso CHECK (tipo_uso IN ('CRONICO', 'AGUDO', 'ESTACIONAL', 'PREVENTIVO')),
    CONSTRAINT chk_estacion CHECK (estacion_pico IS NULL OR estacion_pico IN ('INVIERNO', 'PRIMAVERA', 'VERANO', 'OTOÑO'))
);

-- Índices para clasificación
CREATE INDEX idx_clasif_tipo_uso ON clasificacion_medicamentos(tipo_uso);
CREATE INDEX idx_clasif_estacional ON clasificacion_medicamentos(es_estacional) WHERE es_estacional = TRUE;
CREATE INDEX idx_clasif_categoria ON clasificacion_medicamentos(categoria);

COMMENT ON TABLE clasificacion_medicamentos IS 'Tabla maestra de clasificación de medicamentos por principio activo';
COMMENT ON COLUMN clasificacion_medicamentos.tipo_uso IS 'CRONICO: uso continuo (ej: hipertensión), AGUDO: uso puntual (ej: antibiótico), ESTACIONAL: variación por temporada';

-- ============================================================================
-- 3. TABLA: PRODUCTOS
-- Catálogo de productos de la farmacia
-- ============================================================================
CREATE TABLE productos (
    codigo_producto VARCHAR(50) PRIMARY KEY,
    descripcion VARCHAR(300) NOT NULL,
    medicamento_identificado VARCHAR(300),
    principio_activo VARCHAR(300),
    categoria VARCHAR(150),
    precio_venta DECIMAL(10,2) NOT NULL DEFAULT 0,
    precio_costo DECIMAL(10,2) NOT NULL DEFAULT 0,
    stock_actual INTEGER NOT NULL DEFAULT 0,
    stock_minimo INTEGER DEFAULT 10,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Key a clasificación (opcional, algunos productos sin PA)
    FOREIGN KEY (principio_activo) REFERENCES clasificacion_medicamentos(principio_activo) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT chk_precio_venta CHECK (precio_venta >= 0),
    CONSTRAINT chk_precio_costo CHECK (precio_costo >= 0),
    CONSTRAINT chk_stock CHECK (stock_actual >= 0),
    CONSTRAINT chk_margen CHECK (precio_venta >= precio_costo)
);

-- Índices para productos
CREATE INDEX idx_productos_descripcion ON productos USING gin(descripcion gin_trgm_ops);
CREATE INDEX idx_productos_principio_activo ON productos(principio_activo);
CREATE INDEX idx_productos_categoria ON productos(categoria);
CREATE INDEX idx_productos_stock_bajo ON productos(stock_actual) WHERE stock_actual <= stock_minimo;
CREATE INDEX idx_productos_activo ON productos(activo) WHERE activo = TRUE;

COMMENT ON TABLE productos IS 'Catálogo de productos de la farmacia (1,996 registros iniciales)';
COMMENT ON COLUMN productos.stock_actual IS 'Stock actualizado manualmente vía carga Excel';
COMMENT ON COLUMN productos.stock_minimo IS 'Nivel mínimo para generar alerta de reposición';

-- ============================================================================
-- 4. TABLA: BOLETAS
-- Encabezado de boletas/facturas de venta
-- ============================================================================
CREATE TABLE boletas (
    numero_boleta VARCHAR(20) PRIMARY KEY,
    tipo_documento VARCHAR(50) NOT NULL DEFAULT 'Boleta Electrónica',
    fecha_emision DATE NOT NULL,
    fecha_vencimiento DATE,
    rut_cliente VARCHAR(12) NOT NULL,
    vendedor VARCHAR(150),
    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0,
    descuento_total DECIMAL(10,2) NOT NULL DEFAULT 0,
    iva DECIMAL(10,2) NOT NULL DEFAULT 0,
    total DECIMAL(10,2) NOT NULL DEFAULT 0,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Keys
    FOREIGN KEY (rut_cliente) REFERENCES clientes(rut) ON DELETE RESTRICT,

    -- Constraints
    CONSTRAINT chk_fecha_vencimiento CHECK (fecha_vencimiento IS NULL OR fecha_vencimiento >= fecha_emision),
    CONSTRAINT chk_montos CHECK (subtotal >= 0 AND descuento_total >= 0 AND iva >= 0 AND total >= 0)
);

-- Índices para boletas
CREATE INDEX idx_boletas_fecha ON boletas(fecha_emision DESC);
CREATE INDEX idx_boletas_cliente ON boletas(rut_cliente, fecha_emision DESC);
CREATE INDEX idx_boletas_mes ON boletas(DATE_TRUNC('month', fecha_emision));

COMMENT ON TABLE boletas IS 'Encabezado de boletas de venta (103,871 boletas únicas)';
COMMENT ON COLUMN boletas.total IS 'Total con IVA incluido';

-- ============================================================================
-- 5. TABLA: DETALLE_VENTAS
-- Líneas de detalle de cada boleta (productos vendidos)
-- ============================================================================
CREATE TABLE detalle_ventas (
    id SERIAL PRIMARY KEY,
    numero_boleta VARCHAR(20) NOT NULL,
    codigo_producto VARCHAR(50) NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    precio_unitario DECIMAL(10,2) NOT NULL, -- Con IVA
    descuento DECIMAL(10,2) NOT NULL DEFAULT 0,
    neto DECIMAL(10,2) NOT NULL, -- Sin IVA
    subtotal DECIMAL(10,2) NOT NULL, -- cantidad * precio_unitario - descuento
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Keys
    FOREIGN KEY (numero_boleta) REFERENCES boletas(numero_boleta) ON DELETE CASCADE,
    FOREIGN KEY (codigo_producto) REFERENCES productos(codigo_producto) ON DELETE RESTRICT,

    -- Constraints
    CONSTRAINT chk_cantidad CHECK (cantidad > 0),
    CONSTRAINT chk_precios_detalle CHECK (precio_unitario >= 0 AND descuento >= 0 AND neto >= 0 AND subtotal >= 0),
    CONSTRAINT uq_boleta_producto UNIQUE (numero_boleta, codigo_producto)
);

-- Índices para detalle ventas
CREATE INDEX idx_detalle_boleta ON detalle_ventas(numero_boleta);
CREATE INDEX idx_detalle_producto ON detalle_ventas(codigo_producto);
CREATE INDEX idx_detalle_fecha ON detalle_ventas(fecha_creacion DESC);

COMMENT ON TABLE detalle_ventas IS 'Líneas de detalle de ventas (152,429 transacciones)';
COMMENT ON COLUMN detalle_ventas.precio_unitario IS 'Precio unitario CON IVA incluido';
COMMENT ON COLUMN detalle_ventas.neto IS 'Monto SIN IVA';

-- ============================================================================
-- 6. TABLA: HISTORIAL_STOCK
-- Auditoría de movimientos de stock
-- ============================================================================
CREATE TABLE historial_stock (
    id SERIAL PRIMARY KEY,
    codigo_producto VARCHAR(50) NOT NULL,
    tipo_movimiento VARCHAR(20) NOT NULL, -- VENTA, INGRESO, AJUSTE, DEVOLUCION
    cantidad INTEGER NOT NULL, -- Positivo para ingresos, negativo para salidas
    stock_anterior INTEGER NOT NULL,
    stock_nuevo INTEGER NOT NULL,
    numero_boleta VARCHAR(20), -- Si es por venta
    observaciones TEXT,
    fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario VARCHAR(100),

    -- Foreign Keys
    FOREIGN KEY (codigo_producto) REFERENCES productos(codigo_producto) ON DELETE RESTRICT,
    FOREIGN KEY (numero_boleta) REFERENCES boletas(numero_boleta) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT chk_tipo_movimiento CHECK (tipo_movimiento IN ('VENTA', 'INGRESO', 'AJUSTE', 'DEVOLUCION')),
    CONSTRAINT chk_coherencia_stock CHECK (stock_nuevo = stock_anterior + cantidad)
);

-- Índices para historial stock
CREATE INDEX idx_hist_producto ON historial_stock(codigo_producto, fecha_movimiento DESC);
CREATE INDEX idx_hist_fecha ON historial_stock(fecha_movimiento DESC);
CREATE INDEX idx_hist_tipo ON historial_stock(tipo_movimiento);

COMMENT ON TABLE historial_stock IS 'Auditoría de todos los movimientos de inventario';
COMMENT ON COLUMN historial_stock.cantidad IS 'Positivo=ingreso, Negativo=salida';

-- ============================================================================
-- 7. TABLA: DATOS_ESTACIONALES
-- Datos simulados de demanda estacional (Opción A - MINSAL simulado)
-- ============================================================================
CREATE TABLE datos_estacionales (
    id SERIAL PRIMARY KEY,
    mes INTEGER NOT NULL, -- 1-12
    categoria VARCHAR(150) NOT NULL,
    indice_demanda DECIMAL(4,2) NOT NULL, -- 0-10 (10 = pico máximo)
    estacion VARCHAR(20) NOT NULL,
    descripcion TEXT,
    fuente VARCHAR(100) DEFAULT 'Simulado basado en patrones históricos',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_mes CHECK (mes >= 1 AND mes <= 12),
    CONSTRAINT chk_indice CHECK (indice_demanda >= 0 AND indice_demanda <= 10),
    CONSTRAINT chk_estacion_datos CHECK (estacion IN ('INVIERNO', 'PRIMAVERA', 'VERANO', 'OTOÑO')),
    CONSTRAINT uq_mes_categoria UNIQUE (mes, categoria)
);

-- Índices para datos estacionales
CREATE INDEX idx_estacional_mes ON datos_estacionales(mes);
CREATE INDEX idx_estacional_categoria ON datos_estacionales(categoria);
CREATE INDEX idx_estacional_estacion ON datos_estacionales(estacion);

COMMENT ON TABLE datos_estacionales IS 'Datos simulados de demanda estacional por categoría (48 registros: 12 meses × 4 categorías)';
COMMENT ON COLUMN datos_estacionales.indice_demanda IS 'Índice de demanda esperada (0=mínimo, 10=pico estacional)';

-- ============================================================================
-- 8. TABLA: ALERTAS_CLIENTES
-- Sistema de alertas para abandono de medicamentos o eventos importantes
-- ============================================================================
CREATE TABLE alertas_clientes (
    id SERIAL PRIMARY KEY,
    rut_cliente VARCHAR(12) NOT NULL,
    tipo_alerta VARCHAR(50) NOT NULL, -- ABANDONO_MEDICAMENTO, STOCK_BAJO, CLIENTE_FRECUENTE, CUMPLEAÑOS
    codigo_producto VARCHAR(50),
    prioridad VARCHAR(10) NOT NULL DEFAULT 'MEDIA', -- ALTA, MEDIA, BAJA
    mensaje TEXT NOT NULL,
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_compra DATE,
    dias_sin_compra INTEGER,
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE', -- PENDIENTE, VISTA, RESUELTA, IGNORADA
    fecha_resolucion TIMESTAMP,

    -- Foreign Keys
    FOREIGN KEY (rut_cliente) REFERENCES clientes(rut) ON DELETE CASCADE,
    FOREIGN KEY (codigo_producto) REFERENCES productos(codigo_producto) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT chk_tipo_alerta CHECK (tipo_alerta IN ('ABANDONO_MEDICAMENTO', 'STOCK_BAJO', 'CLIENTE_FRECUENTE', 'CUMPLEAÑOS', 'PROMOCION')),
    CONSTRAINT chk_prioridad CHECK (prioridad IN ('ALTA', 'MEDIA', 'BAJA')),
    CONSTRAINT chk_estado_alerta CHECK (estado IN ('PENDIENTE', 'VISTA', 'RESUELTA', 'IGNORADA'))
);

-- Índices para alertas
CREATE INDEX idx_alertas_cliente ON alertas_clientes(rut_cliente, fecha_generacion DESC);
CREATE INDEX idx_alertas_estado ON alertas_clientes(estado) WHERE estado = 'PENDIENTE';
CREATE INDEX idx_alertas_prioridad ON alertas_clientes(prioridad, fecha_generacion DESC);
CREATE INDEX idx_alertas_tipo ON alertas_clientes(tipo_alerta);

COMMENT ON TABLE alertas_clientes IS 'Sistema de alertas para seguimiento de clientes';
COMMENT ON COLUMN alertas_clientes.dias_sin_compra IS 'Días transcurridos desde última compra del medicamento';

-- ============================================================================
-- 9. VISTA: SEGMENTACION_CLIENTES
-- Vista materializada para análisis de segmentación de clientes
-- ============================================================================
CREATE MATERIALIZED VIEW mv_segmentacion_clientes AS
WITH cliente_medicamentos AS (
    SELECT
        b.rut_cliente,
        c.nombre as nombre_cliente,
        p.principio_activo,
        p.categoria,
        cm.tipo_uso,
        COUNT(DISTINCT b.numero_boleta) as total_compras,
        SUM(dv.cantidad) as cantidad_total,
        MIN(b.fecha_emision) as primera_compra,
        MAX(b.fecha_emision) as ultima_compra,
        SUM(dv.subtotal) as gasto_total,
        ROUND(AVG(EXTRACT(EPOCH FROM (b.fecha_emision - LAG(b.fecha_emision)
            OVER (PARTITION BY b.rut_cliente, p.codigo_producto ORDER BY b.fecha_emision)))/86400)) as dias_promedio_entre_compras
    FROM boletas b
    INNER JOIN detalle_ventas dv ON b.numero_boleta = dv.numero_boleta
    INNER JOIN productos p ON dv.codigo_producto = p.codigo_producto
    INNER JOIN clientes c ON b.rut_cliente = c.rut
    LEFT JOIN clasificacion_medicamentos cm ON p.principio_activo = cm.principio_activo
    WHERE p.principio_activo IS NOT NULL AND p.principio_activo != ''
    GROUP BY b.rut_cliente, c.nombre, p.principio_activo, p.categoria, cm.tipo_uso
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

-- Índices para la vista materializada
CREATE UNIQUE INDEX idx_mv_seg_cliente_producto ON mv_segmentacion_clientes(rut_cliente, principio_activo);
CREATE INDEX idx_mv_seg_segmento ON mv_segmentacion_clientes(segmento_cliente);
CREATE INDEX idx_mv_seg_tipo_uso ON mv_segmentacion_clientes(tipo_uso);
CREATE INDEX idx_mv_seg_dias_sin_compra ON mv_segmentacion_clientes(dias_sin_compra DESC);

COMMENT ON MATERIALIZED VIEW mv_segmentacion_clientes IS 'Segmentación de clientes por tipo de medicamento y patrón de compra';

-- ============================================================================
-- 10. VISTA: ANALISIS_ESTACIONAL
-- Vista para análisis de ventas estacionales
-- ============================================================================
CREATE MATERIALIZED VIEW mv_analisis_estacional AS
SELECT
    EXTRACT(MONTH FROM b.fecha_emision)::INTEGER as mes,
    EXTRACT(YEAR FROM b.fecha_emision)::INTEGER as anio,
    CASE
        WHEN EXTRACT(MONTH FROM b.fecha_emision) IN (6,7,8) THEN 'INVIERNO'
        WHEN EXTRACT(MONTH FROM b.fecha_emision) IN (9,10,11) THEN 'PRIMAVERA'
        WHEN EXTRACT(MONTH FROM b.fecha_emision) IN (12,1,2) THEN 'VERANO'
        ELSE 'OTOÑO'
    END as estacion,
    p.categoria,
    cm.es_estacional,
    COUNT(DISTINCT b.numero_boleta) as total_boletas,
    SUM(dv.cantidad) as unidades_vendidas,
    SUM(dv.subtotal) as ventas_totales,
    AVG(dv.subtotal) as ticket_promedio,
    COUNT(DISTINCT b.rut_cliente) as clientes_unicos
FROM boletas b
INNER JOIN detalle_ventas dv ON b.numero_boleta = dv.numero_boleta
INNER JOIN productos p ON dv.codigo_producto = p.codigo_producto
LEFT JOIN clasificacion_medicamentos cm ON p.principio_activo = cm.principio_activo
WHERE p.categoria IS NOT NULL AND p.categoria != ''
GROUP BY
    EXTRACT(MONTH FROM b.fecha_emision),
    EXTRACT(YEAR FROM b.fecha_emision),
    CASE
        WHEN EXTRACT(MONTH FROM b.fecha_emision) IN (6,7,8) THEN 'INVIERNO'
        WHEN EXTRACT(MONTH FROM b.fecha_emision) IN (9,10,11) THEN 'PRIMAVERA'
        WHEN EXTRACT(MONTH FROM b.fecha_emision) IN (12,1,2) THEN 'VERANO'
        ELSE 'OTOÑO'
    END,
    p.categoria,
    cm.es_estacional;

-- Índices para análisis estacional
CREATE INDEX idx_mv_estacional_mes ON mv_analisis_estacional(anio, mes);
CREATE INDEX idx_mv_estacional_categoria ON mv_analisis_estacional(categoria);
CREATE INDEX idx_mv_estacional_estacion ON mv_analisis_estacional(estacion);

COMMENT ON MATERIALIZED VIEW mv_analisis_estacional IS 'Análisis de ventas por estación y categoría para predicción de demanda';

-- ============================================================================
-- FUNCIONES Y TRIGGERS
-- ============================================================================

-- Función para actualizar fecha_actualizacion
CREATE OR REPLACE FUNCTION actualizar_fecha_modificacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para actualización automática de fechas
CREATE TRIGGER trg_clientes_actualizacion
    BEFORE UPDATE ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_modificacion();

CREATE TRIGGER trg_productos_actualizacion
    BEFORE UPDATE ON productos
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_modificacion();

CREATE TRIGGER trg_clasificacion_actualizacion
    BEFORE UPDATE ON clasificacion_medicamentos
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_modificacion();

-- Función para actualizar stock después de venta
CREATE OR REPLACE FUNCTION actualizar_stock_venta()
RETURNS TRIGGER AS $$
BEGIN
    -- Insertar en historial de stock
    INSERT INTO historial_stock (
        codigo_producto,
        tipo_movimiento,
        cantidad,
        stock_anterior,
        stock_nuevo,
        numero_boleta,
        usuario
    )
    SELECT
        NEW.codigo_producto,
        'VENTA',
        -NEW.cantidad,
        p.stock_actual,
        p.stock_actual - NEW.cantidad,
        NEW.numero_boleta,
        CURRENT_USER
    FROM productos p
    WHERE p.codigo_producto = NEW.codigo_producto;

    -- Actualizar stock actual
    UPDATE productos
    SET stock_actual = stock_actual - NEW.cantidad,
        fecha_actualizacion = CURRENT_TIMESTAMP
    WHERE codigo_producto = NEW.codigo_producto;

    -- Generar alerta si stock bajo
    INSERT INTO alertas_clientes (
        rut_cliente,
        tipo_alerta,
        codigo_producto,
        prioridad,
        mensaje
    )
    SELECT
        b.rut_cliente,
        'STOCK_BAJO',
        p.codigo_producto,
        'ALTA',
        'El producto ' || p.descripcion || ' tiene stock bajo (' || p.stock_actual || ' unidades)'
    FROM productos p
    INNER JOIN boletas b ON b.numero_boleta = NEW.numero_boleta
    WHERE p.codigo_producto = NEW.codigo_producto
    AND p.stock_actual <= p.stock_minimo;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualización automática de stock
CREATE TRIGGER trg_detalle_ventas_stock
    AFTER INSERT ON detalle_ventas
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_stock_venta();

-- Función para calcular totales de boleta
CREATE OR REPLACE FUNCTION calcular_totales_boleta()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE boletas
    SET
        subtotal = (SELECT COALESCE(SUM(subtotal), 0) FROM detalle_ventas WHERE numero_boleta = NEW.numero_boleta),
        descuento_total = (SELECT COALESCE(SUM(descuento), 0) FROM detalle_ventas WHERE numero_boleta = NEW.numero_boleta),
        iva = (SELECT COALESCE(SUM(subtotal), 0) FROM detalle_ventas WHERE numero_boleta = NEW.numero_boleta) * 0.19,
        total = (SELECT COALESCE(SUM(subtotal), 0) FROM detalle_ventas WHERE numero_boleta = NEW.numero_boleta) * 1.19
    WHERE numero_boleta = NEW.numero_boleta;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualización de totales
CREATE TRIGGER trg_actualizar_totales_boleta
    AFTER INSERT OR UPDATE ON detalle_ventas
    FOR EACH ROW
    EXECUTE FUNCTION calcular_totales_boleta();

-- Función para refrescar vistas materializadas
CREATE OR REPLACE FUNCTION refrescar_vistas_materializadas()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_segmentacion_clientes;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_analisis_estacional;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refrescar_vistas_materializadas IS 'Refresca todas las vistas materializadas. Ejecutar diariamente o después de cargas de datos';

-- ============================================================================
-- FIN DEL ESQUEMA
-- ============================================================================
