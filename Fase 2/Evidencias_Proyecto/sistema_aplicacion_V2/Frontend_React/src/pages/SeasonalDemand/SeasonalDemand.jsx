import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, BarChart, Bar, Area, ComposedChart, Cell
} from 'recharts';
import './SeasonalDemand.css';
// Actualizado - alerta removida

const SeasonalDemand = () => {
  const [categorias, setCategorias] = useState([]);
  const [categoriaSeleccionada, setCategoriaSeleccionada] = useState('');
  const [año, setAño] = useState(new Date().getFullYear() + 1);
  const [predicciones, setPredicciones] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Cargar categorías disponibles
  useEffect(() => {
    const fetchCategorias = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/seasonal/categories/');
        const data = await response.json();
        setCategorias(data.categorias || []);

        if (data.categorias && data.categorias.length > 0) {
          setCategoriaSeleccionada(data.categorias[0]);
        }
      } catch (err) {
        console.error('Error cargando categorías:', err);
        setError('No se pudieron cargar las categorías');
      }
    };

    fetchCategorias();
  }, []);

  // Función para cargar predicciones (memoizada con useCallback)
  const fetchPredicciones = useCallback(async () => {
    if (!categoriaSeleccionada) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/api/seasonal/year/?categoria=${categoriaSeleccionada}&año=${año}`
      );

      if (!response.ok) {
        throw new Error('Error al obtener predicciones');
      }

      const data = await response.json();
      setPredicciones(data);
    } catch (err) {
      console.error('Error:', err);
      setError('No se pudieron cargar las predicciones. Verifica que el backend esté funcionando.');
    } finally {
      setLoading(false);
    }
  }, [categoriaSeleccionada, año]);

  // Cargar predicciones cuando cambie la categoría o año
  useEffect(() => {
    fetchPredicciones();
  }, [fetchPredicciones]);

  // Preparar datos para gráfico combinado (histórico + predicciones)
  // IMPORTANTE: Ordenar explícitamente por mes_numero para garantizar orden Enero->Diciembre
  const chartData = (predicciones?.predicciones || [])
    .map(p => ({
      mes: p.mes_nombre?.substring(0, 3) || 'N/A',
      prediccion: p.prediccion,
      min: p.intervalo_confianza?.min || 0,
      max: p.intervalo_confianza?.max || 0,
      mes_numero: p.mes,
      tendencia: p.tendencia
    }))
    .sort((a, b) => a.mes_numero - b.mes_numero); // Forzar orden 1->12

  // Debug: Verificar orden de meses
  console.log('🔍 Orden de meses en chartData:', chartData.map(d => `${d.mes}(${d.mes_numero})`).join(', '));

  // Datos históricos si existen
  const historicoData = predicciones?.historico?.map(h => ({
    mes: h.mes_nombre?.substring(0, 3) || 'N/A',
    historico: h.transacciones,
    mes_numero: h.mes
  })) || [];

  // Combinar histórico y predicciones para visualización comparativa
  // Usar mes_numero para hacer el match más preciso
  // Ya está ordenado en chartData, no es necesario volver a ordenar
  const dataCombinada = chartData.map(pred => {
    const hist = historicoData.find(h => h.mes_numero === pred.mes_numero);
    return {
      ...pred,
      historico: hist?.historico || null
    };
  });

  const estadisticas = predicciones?.estadisticas || {};
  const tieneDatosReales = predicciones?.tiene_datos_reales || false;

  return (
    <div className="seasonal-demand-container">
      <div className="seasonal-header">
        <h2>📊 Análisis Predictivo de Demanda Estacional</h2>
        <p className="subtitle">
          Predicciones iterativas con Machine Learning (Random Forest) - Actualización dinámica de lags
        </p>
        <div className="badge-historico">
          ✅ Basado en datos históricos reales
        </div>
      </div>

      <div className="controls-panel">
        <div className="control-group">
          <label>Categoría Médica:</label>
          <select
            value={categoriaSeleccionada}
            onChange={(e) => setCategoriaSeleccionada(e.target.value)}
            className="select-input"
          >
            {categorias.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Año a Predecir:</label>
          <select
            value={año}
            onChange={(e) => setAño(parseInt(e.target.value))}
            className="select-input"
          >
            <option value={2026}>2026</option>
            <option value={2027}>2027</option>
            <option value={2028}>2028</option>
          </select>
        </div>

        <button
          onClick={fetchPredicciones}
          className="btn-refresh"
          disabled={loading}
        >
          {loading ? '🔄 Cargando...' : '🔄 Actualizar'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {loading && (
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Calculando predicciones iterativas...</p>
        </div>
      )}

      {!loading && predicciones && (
        <>
          <div className="kpis-grid">
            <div className="kpi-card">
              <div className="kpi-icon">📈</div>
              <div className="kpi-content">
                <h3>Demanda Anual Proyectada</h3>
                <p className="kpi-value">
                  {estadisticas.total_anual_proyectado?.toLocaleString() || 'N/A'}
                </p>
                <span className="kpi-label">transacciones totales</span>
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-icon">📊</div>
              <div className="kpi-content">
                <h3>Promedio Mensual</h3>
                <p className="kpi-value">
                  {estadisticas.promedio_mensual?.toLocaleString() || 'N/A'}
                </p>
                <span className="kpi-label">transacciones/mes</span>
              </div>
            </div>

            <div className="kpi-card highlight">
              <div className="kpi-icon">🔥</div>
              <div className="kpi-content">
                <h3>Mes de Mayor Demanda</h3>
                <p className="kpi-value">{estadisticas.mes_mayor_demanda?.mes || 'N/A'}</p>
                <span className="kpi-label">
                  {estadisticas.mes_mayor_demanda?.transacciones?.toLocaleString() || '0'} transacciones
                </span>
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-icon">📉</div>
              <div className="kpi-content">
                <h3>Mes de Menor Demanda</h3>
                <p className="kpi-value">{estadisticas.mes_menor_demanda?.mes || 'N/A'}</p>
                <span className="kpi-label">
                  {estadisticas.mes_menor_demanda?.transacciones?.toLocaleString() || '0'} transacciones
                </span>
              </div>
            </div>
          </div>

          <div className="estadisticas-adicionales">
            <div className="stat-item">
              <span className="stat-label">Variabilidad Estacional:</span>
              <span className="stat-value">{estadisticas.variabilidad_porcentaje || 0}%</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Interpretación:</span>
              <span className="stat-value">{estadisticas.interpretacion || 'N/A'}</span>
            </div>
          </div>

          {/* Gráfico principal con intervalo de confianza */}
          <div className="chart-container">
            <h3>Tendencia de Demanda Mensual con Intervalo de Confianza</h3>
            <p className="chart-subtitle">
              Línea azul: Predicción | Área sombreada: Intervalo de confianza (±20-30%)
            </p>
            <ResponsiveContainer width="100%" height={350}>
              <ComposedChart data={dataCombinada}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="mes" />
                <YAxis />
                <Tooltip
                  formatter={(value, name) => {
                    if (name === 'Predicción') return [`${value} transacciones`, 'Predicción'];
                    if (name === 'Histórico Real') return [`${value} transacciones`, 'Histórico Real'];
                    if (name === 'Intervalo Superior') return [`${value} transacciones`, 'Máximo'];
                    if (name === 'Intervalo Inferior') return [`${value} transacciones`, 'Mínimo'];
                    return [value, name];
                  }}
                />
                <Legend />

                {/* Área de intervalo de confianza */}
                <Area
                  type="monotone"
                  dataKey="max"
                  stackId="1"
                  stroke="none"
                  fill="#8884d8"
                  fillOpacity={0.1}
                  name="Intervalo Superior"
                />
                <Area
                  type="monotone"
                  dataKey="min"
                  stackId="1"
                  stroke="none"
                  fill="#8884d8"
                  fillOpacity={0.1}
                  name="Intervalo Inferior"
                />

                {/* Datos históricos si existen */}
                {tieneDatosReales && (
                  <Line
                    type="monotone"
                    dataKey="historico"
                    stroke="#82ca9d"
                    strokeWidth={2}
                    dot={{ fill: '#82ca9d', r: 4 }}
                    name="Histórico Real"
                    connectNulls
                  />
                )}

                {/* Predicción */}
                <Line
                  type="monotone"
                  dataKey="prediccion"
                  stroke="#8884d8"
                  strokeWidth={3}
                  dot={{ fill: '#8884d8', r: 5 }}
                  activeDot={{ r: 8 }}
                  name="Predicción"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Gráfico de barras con tendencias */}
          <div className="chart-container">
            <h3>Comparación Mensual por Tendencia</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dataCombinada}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="mes" />
                <YAxis />
                <Tooltip
                  formatter={(value, name, props) => {
                    const tendencia = props.payload.tendencia;
                    return [`${value} transacciones (${tendencia})`, 'Predicción'];
                  }}
                />
                <Legend />
                <Bar
                  dataKey="prediccion"
                  fill="#8884d8"
                  name="Transacciones Proyectadas"
                >
                  {dataCombinada.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        entry.tendencia === 'ALTA' ? '#ff6b6b' :
                        entry.tendencia === 'BAJA' ? '#4ecdc4' :
                        '#95e1d3'
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="legend-tendencias">
              <span className="legend-item"><span className="color-box" style={{backgroundColor: '#ff6b6b'}}></span> ALTA</span>
              <span className="legend-item"><span className="color-box" style={{backgroundColor: '#95e1d3'}}></span> NORMAL</span>
              <span className="legend-item"><span className="color-box" style={{backgroundColor: '#4ecdc4'}}></span> BAJA</span>
            </div>
          </div>

          {/* Recomendaciones de inventario */}
          <div className="recommendations-panel">
            <h3>💡 Recomendaciones de Inventario (Top 3 Meses)</h3>
            <div className="recommendations-grid">
              {dataCombinada
                .sort((a, b) => b.prediccion - a.prediccion)
                .slice(0, 3)
                .map((mes, index) => (
                  <div key={mes.mes_numero} className="recommendation-card">
                    <div className="recommendation-rank">#{index + 1}</div>
                    <h4>{mes.mes}</h4>
                    <p className="recommendation-value">
                      {mes.prediccion.toLocaleString()} transacciones
                    </p>
                    <p className="recommendation-range">
                      Rango: {mes.min.toLocaleString()} - {mes.max.toLocaleString()}
                    </p>
                    <p className="recommendation-action">
                      {mes.prediccion > (estadisticas.promedio_mensual || 0) * 1.3
                        ? '⬆️ Aumentar stock significativamente (+30%)'
                        : mes.prediccion > (estadisticas.promedio_mensual || 0) * 1.1
                        ? '↗️ Aumentar stock moderadamente (+10-30%)'
                        : '✅ Mantener stock normal'
                      }
                    </p>
                    <span className={`badge-tendencia ${mes.tendencia.toLowerCase()}`}>
                      {mes.tendencia}
                    </span>
                  </div>
                ))}
            </div>
          </div>

          {/* Tabla detallada */}
          <div className="table-container">
            <h3>📋 Detalle Mensual Completo</h3>
            <table className="predicciones-table">
              <thead>
                <tr>
                  <th>Mes</th>
                  {tieneDatosReales && <th>Histórico Real</th>}
                  <th>Predicción</th>
                  <th>Intervalo Confianza</th>
                  <th>Tendencia</th>
                  <th>Acción Sugerida</th>
                </tr>
              </thead>
              <tbody>
                {dataCombinada.map((mes) => (
                  <tr key={mes.mes_numero}>
                    <td className="mes-nombre">{mes.mes}</td>
                    {tieneDatosReales && (
                      <td className="historico-value">
                        {mes.historico ? mes.historico.toLocaleString() : '-'}
                      </td>
                    )}
                    <td className="prediccion-value">{mes.prediccion.toLocaleString()}</td>
                    <td className="intervalo-value">
                      {mes.min.toLocaleString()} - {mes.max.toLocaleString()}
                    </td>
                    <td>
                      <span className={`badge-tendencia ${mes.tendencia.toLowerCase()}`}>
                        {mes.tendencia}
                      </span>
                    </td>
                    <td className="accion-sugerida">
                      {mes.prediccion > (estadisticas.promedio_mensual || 0) * 1.3
                        ? 'Aumentar stock significativamente'
                        : mes.prediccion > (estadisticas.promedio_mensual || 0) * 1.1
                        ? 'Aumentar stock moderadamente'
                        : mes.prediccion < (estadisticas.promedio_mensual || 0) * 0.8
                        ? 'Considerar reducción de stock'
                        : 'Mantener stock actual'
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};

export default SeasonalDemand;
