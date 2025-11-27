import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, BarChart, Bar
} from 'recharts';
import './SeasonalDemand.css';

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

  // Cargar predicciones cuando cambie la categoría o año
  useEffect(() => {
    if (categoriaSeleccionada) {
      fetchPredicciones();
    }
  }, [categoriaSeleccionada, año]);

  const fetchPredicciones = async () => {
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
      setError('No se pudieron cargar las predicciones');
    } finally {
      setLoading(false);
    }
  };

  const chartData = predicciones?.predicciones?.map(p => ({
    mes: p.mes_nombre?.substring(0, 3) || 'N/A',
    prediccion: p.prediccion,
    mes_numero: p.mes
  })) || [];

  const mesMayorDemanda = (chartData && chartData.length > 0)
    ? chartData.reduce((max, current) =>
        current.prediccion > max.prediccion ? current : max
      , { prediccion: 0, mes: '' })
    : { prediccion: 0, mes: 'N/A' };

  const promedio = predicciones ? 
    predicciones.total_anual_proyectado / 12 : 0;

  return (
    <div className="seasonal-demand-container">
      <div className="seasonal-header">
        <h2>📊 Análisis Predictivo de Demanda Estacional</h2>
        <p className="subtitle">
          Predicciones basadas en Random Forest con datos históricos
        </p>
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
          <p>Calculando predicciones...</p>
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
                  {predicciones.total_anual_proyectado.toLocaleString()}
                </p>
                <span className="kpi-label">transacciones</span>
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-icon">📊</div>
              <div className="kpi-content">
                <h3>Promedio Mensual</h3>
                <p className="kpi-value">
                  {Math.round(promedio).toLocaleString()}
                </p>
                <span className="kpi-label">transacciones/mes</span>
              </div>
            </div>

            <div className="kpi-card highlight">
              <div className="kpi-icon">🔥</div>
              <div className="kpi-content">
                <h3>Mes de Mayor Demanda</h3>
                <p className="kpi-value">{mesMayorDemanda.mes}</p>
                <span className="kpi-label">
                  {mesMayorDemanda.prediccion} transacciones
                </span>
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-icon">🎯</div>
              <div className="kpi-content">
                <h3>Categoría</h3>
                <p className="kpi-value-small">{categoriaSeleccionada}</p>
                <span className="kpi-label">Año {año}</span>
              </div>
            </div>
          </div>

          <div className="chart-container">
            <h3>Tendencia de Demanda Mensual</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="mes" />
                <YAxis />
                <Tooltip 
                  formatter={(value) => [`${value} transacciones`, 'Predicción']}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="prediccion" 
                  stroke="#8884d8" 
                  strokeWidth={3}
                  dot={{ fill: '#8884d8', r: 5 }}
                  activeDot={{ r: 8 }}
                  name="Demanda Proyectada"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Comparación Mensual</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="mes" />
                <YAxis />
                <Tooltip 
                  formatter={(value) => [`${value} transacciones`, 'Predicción']}
                />
                <Legend />
                <Bar 
                  dataKey="prediccion" 
                  fill="#82ca9d" 
                  name="Transacciones Proyectadas"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="recommendations-panel">
            <h3>💡 Recomendaciones de Inventario</h3>
            <div className="recommendations-grid">
              {chartData
                .sort((a, b) => b.prediccion - a.prediccion)
                .slice(0, 3)
                .map((mes, index) => (
                  <div key={mes.mes_numero} className="recommendation-card">
                    <div className="recommendation-rank">#{index + 1}</div>
                    <h4>{mes.mes}</h4>
                    <p className="recommendation-value">
                      {mes.prediccion} transacciones
                    </p>
                    <p className="recommendation-action">
                      {mes.prediccion > promedio * 1.3 
                        ? '⬆️ Aumentar stock significativamente'
                        : mes.prediccion > promedio * 1.1
                        ? '↗️ Aumentar stock moderadamente'
                        : '✅ Mantener stock normal'
                      }
                    </p>
                  </div>
                ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SeasonalDemand;