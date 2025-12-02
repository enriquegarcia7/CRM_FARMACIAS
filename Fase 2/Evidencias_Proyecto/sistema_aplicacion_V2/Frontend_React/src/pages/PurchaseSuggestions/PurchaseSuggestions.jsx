import { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  RefreshCw,
  ShoppingCart,
  Package,
  Filter,
  Tag,
  Clock,
  FileDown
} from 'lucide-react';
import { sugerenciasService } from '../../services/api';

// ============================================================
// CACHE GLOBAL - Persiste entre cambios de vista/navegación
// ============================================================
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutos
const globalCache = {
  data: null,
  timestamp: null
};

// Skeleton para carga
const SkeletonRow = () => (
  <tr className="animate-pulse">
    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-3/4"></div></td>
    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-20"></div></td>
    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-24"></div></td>
    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-20"></div></td>
  </tr>
);

const SkeletonCard = () => (
  <div className="bg-gray-100 rounded-lg shadow p-6 animate-pulse">
    <div className="flex items-center justify-between">
      <div>
        <div className="h-4 bg-gray-300 rounded w-24 mb-2"></div>
        <div className="h-8 bg-gray-300 rounded w-16 mt-2"></div>
        <div className="h-3 bg-gray-300 rounded w-32 mt-2"></div>
      </div>
      <div className="h-10 w-10 bg-gray-300 rounded-full"></div>
    </div>
  </div>
);

const PurchaseSuggestions = () => {
  // Inicializar estado desde cache global si existe y es válido
  const getCachedData = () => {
    if (globalCache.data && globalCache.timestamp) {
      const cacheAge = Date.now() - globalCache.timestamp;
      if (cacheAge < CACHE_DURATION) {
        return globalCache.data;
      }
    }
    return null;
  };

  const cachedData = getCachedData();
  const [sugerencias, setSugerencias] = useState(cachedData?.sugerencias || []);
  const [resumen, setResumen] = useState(cachedData?.resumen || { total_productos: 0, con_oferta: 0, sin_oferta: 0, criticos: 0, altos: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Cargar sugerencias usando el endpoint rápido (con cache global)
  const cargarSugerencias = useCallback(async (forceRefresh = false) => {
    // Si hay cache válido y no es refresh forzado, usar cache
    if (!forceRefresh && globalCache.data && globalCache.timestamp) {
      const cacheAge = Date.now() - globalCache.timestamp;
      if (cacheAge < CACHE_DURATION) {
        setSugerencias(globalCache.data.sugerencias || []);
        setResumen(globalCache.data.resumen || { total_productos: 0, con_oferta: 0, sin_oferta: 0, criticos: 0, altos: 0 });
        return;
      }
    }

    try {
      setLoading(true);
      setError(null);

      const response = await sugerenciasService.rapido({ limite: 100 });

      if (response.data.success) {
        const newData = {
          sugerencias: response.data.sugerencias || [],
          resumen: response.data.resumen || { total_productos: 0, con_oferta: 0, sin_oferta: 0, criticos: 0, altos: 0 }
        };

        // Guardar en cache GLOBAL
        globalCache.data = newData;
        globalCache.timestamp = Date.now();

        setSugerencias(newData.sugerencias);
        setResumen(newData.resumen);
      } else {
        setError(response.data.error || 'Error al cargar sugerencias');
      }

    } catch (err) {
      console.error('Error cargando sugerencias:', err);
      setError(err.response?.data?.error || err.message || 'Error al cargar sugerencias');
    } finally {
      setLoading(false);
    }
  }, []);

  // Cargar datos al montar - solo si no hay cache válido
  useEffect(() => {
    if (!cachedData) {
      cargarSugerencias();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Función para generar y descargar CSVs por proveedor
  const generarCSVsPorProveedor = () => {
    const proveedores = {
      'MEDIVEN': [],
      'PROVEFARMA': [],
      'OTROS': []
    };

    // Clasificar sugerencias por proveedor
    sugerencias.forEach(item => {
      const proveedor = (item.proveedor || '').toUpperCase();
      const registro = {
        codigo: item.producto?.codigo || '',
        nombre: item.producto?.nombre || '',
        cantidad: item.cantidad_sugerida || 0,
        precio: item.oferta?.precio_oferta || item.oferta?.precio_lista || 0
      };

      if (proveedor.includes('MEDIVEN')) {
        proveedores['MEDIVEN'].push(registro);
      } else if (proveedor.includes('PROVEFARMA')) {
        proveedores['PROVEFARMA'].push(registro);
      } else {
        proveedores['OTROS'].push(registro);
      }
    });

    // Generar y descargar CSV para cada proveedor que tenga datos
    const generarCSV = (datos, nombreProveedor) => {
      if (datos.length === 0) return;

      const headers = ['Codigo', 'Nombre Producto', 'Cantidad', 'Precio'];
      const csvContent = [
        headers.join(';'),
        ...datos.map(row =>
          [row.codigo, `"${row.nombre}"`, row.cantidad, row.precio].join(';')
        )
      ].join('\n');

      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `sugerencias_compra_${nombreProveedor.toLowerCase()}_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    };

    // Descargar archivos automáticamente
    setTimeout(() => generarCSV(proveedores['MEDIVEN'], 'MEDIVEN'), 100);
    setTimeout(() => generarCSV(proveedores['PROVEFARMA'], 'PROVEFARMA'), 300);
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(value || 0);
  };

  const getPrioridadColor = (prioridad) => {
    switch (prioridad) {
      case 'critica': return 'bg-red-100 text-red-800 border-red-300';
      case 'alta': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'media': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'baja': return 'bg-green-100 text-green-800 border-green-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getMatchScoreColor = (score) => {
    if (score >= 100) return 'text-green-600'; // Mapping exacto
    if (score >= 80) return 'text-blue-600';   // Muy buena coincidencia
    if (score >= 60) return 'text-yellow-600'; // Coincidencia aceptable
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Sugerencias de Compra</h1>
        <div className="flex gap-3">
          <button
            onClick={generarCSVsPorProveedor}
            disabled={loading || sugerencias.length === 0}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <FileDown size={20} /> Generar CSV Proveedores
          </button>
          <button
            onClick={() => cargarSugerencias(true)}
            disabled={loading}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg transition-colors"
          >
            {loading ? (
              <><RefreshCw size={20} className="animate-spin" /> Cargando...</>
            ) : (
              <><RefreshCw size={20} /> Actualizar</>
            )}
          </button>
        </div>
      </div>

      {/* Tarjetas de resumen */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {loading ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : (
          <>
            {/* Total productos */}
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 font-medium">Total Productos</p>
                  <p className="text-3xl font-bold text-blue-600 mt-2">{resumen.total_productos}</p>
                  <p className="text-sm text-gray-500 mt-1">con demanda y bajo stock</p>
                </div>
                <Package size={40} className="text-blue-400" />
              </div>
            </div>

            {/* Críticos */}
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 font-medium">Críticos</p>
                  <p className="text-3xl font-bold text-red-600 mt-2">{resumen.criticos}</p>
                  <p className="text-sm text-gray-500 mt-1">&lt; 7 días de stock</p>
                </div>
                <AlertTriangle size={40} className="text-red-400" />
              </div>
            </div>

            {/* Con oferta */}
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 font-medium">Con Oferta</p>
                  <p className="text-3xl font-bold text-green-600 mt-2">{resumen.con_oferta}</p>
                  <p className="text-sm text-gray-500 mt-1">ofertas encontradas</p>
                </div>
                <Tag size={40} className="text-green-400" />
              </div>
            </div>
          </>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="text-red-500" />
          <span className="text-red-700">{error}</span>
          <button onClick={cargarSugerencias} className="ml-auto text-red-600 hover:text-red-800 font-medium">
            Reintentar
          </button>
        </div>
      )}

      {/* Tabla de sugerencias */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
          <div className="flex items-center gap-2">
            <ShoppingCart size={24} className="text-blue-600" />
            <h2 className="text-xl font-semibold">Productos a Comprar</h2>
            <span className="text-sm text-gray-500 ml-2">
              ({sugerencias.length} sugerencias con demanda justificada)
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Producto</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Demanda</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Comprar</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Proveedor</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Oferta</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Prioridad</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                [...Array(10)].map((_, i) => <SkeletonRow key={i} />)
              ) : sugerencias.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-6 py-12 text-center text-gray-500">
                    <div className="flex flex-col items-center gap-3">
                      <Filter size={48} className="text-gray-300" />
                      <p className="text-lg font-medium">No hay sugerencias de compra</p>
                      <p className="text-sm">Todos los productos con demanda tienen stock suficiente</p>
                    </div>
                  </td>
                </tr>
              ) : (
                sugerencias.map((item, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    {/* Código */}
                    <td className="px-4 py-4">
                      <p className="text-sm font-mono font-medium text-gray-700">
                        {item.producto?.codigo || '-'}
                      </p>
                    </td>

                    {/* Producto */}
                    <td className="px-4 py-4">
                      <div className="max-w-xs">
                        <p className="text-sm font-medium text-gray-900 truncate" title={item.producto?.nombre}>
                          {item.producto?.nombre || 'Sin nombre'}
                        </p>
                        {item.producto?.categoria && (
                          <span className="inline-block mt-1 px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                            {item.producto.categoria}
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Stock */}
                    <td className="px-4 py-4">
                      <div className="text-center">
                        <p className={`text-sm font-bold ${item.stock?.actual < 5 ? 'text-red-600' : 'text-orange-600'}`}>
                          {item.stock?.actual || 0} / {item.stock?.minimo || 0} mín
                        </p>
                      </div>
                    </td>

                    {/* Demanda */}
                    <td className="px-4 py-4">
                      <div className="text-sm">
                        <p className="font-medium text-gray-900">
                          {item.demanda?.total_90_dias || 0} <span className="text-xs text-gray-500">/ 90 días</span>
                        </p>
                        {item.demanda?.dias_cobertura !== null && (
                          <p className={`text-xs ${item.demanda.dias_cobertura < 7 ? 'text-red-600' : item.demanda.dias_cobertura < 14 ? 'text-orange-600' : 'text-gray-500'}`}>
                            <Clock size={12} className="inline mr-1" />
                            {item.demanda.dias_cobertura} días cobertura
                          </p>
                        )}
                      </div>
                    </td>

                    {/* Cantidad a comprar */}
                    <td className="px-4 py-4">
                      <div className="text-center">
                        <p className="text-lg font-bold text-blue-600">
                          {item.cantidad_sugerida}
                        </p>
                        {item.estacional?.ajuste_aplicado && (
                          <div className="mt-1">
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-orange-100 text-orange-700 text-xs font-medium rounded-full border border-orange-300">
                              📈 +{item.estacional.cantidad_extra} estacional
                            </span>
                            <p className="text-xs text-orange-600 mt-0.5">
                              {item.estacional.mes_proximo}: Alta demanda
                            </p>
                          </div>
                        )}
                      </div>
                    </td>

                    {/* Proveedor */}
                    <td className="px-4 py-4">
                      <p className="text-sm font-medium text-gray-900">
                        {item.proveedor || 'Sin proveedor'}
                      </p>
                    </td>

                    {/* Oferta */}
                    <td className="px-4 py-4">
                      {item.oferta ? (
                        <div className="text-sm">
                          <div className="flex items-center gap-1">
                            <span className="text-green-600 font-bold">
                              {formatCurrency(item.oferta.precio_oferta)}
                            </span>
                            {item.oferta.descuento > 0 && (
                              <span className="bg-green-100 text-green-800 px-1.5 py-0.5 rounded text-xs font-medium">
                                -{item.oferta.descuento}%
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-gray-400 line-through">
                            {formatCurrency(item.oferta.precio_lista)}
                          </p>
                          {item.oferta.codigo && (
                            <p className="text-xs text-blue-600 font-mono">
                              Cód: {item.oferta.codigo}
                            </p>
                          )}
                          <p className="text-xs text-gray-500 truncate max-w-[150px]" title={item.oferta.nombre}>
                            {item.oferta.nombre}
                          </p>
                          {item.oferta.dias_vigencia !== undefined && (
                            <p className={`text-xs ${item.oferta.dias_vigencia < 7 ? 'text-red-500' : 'text-gray-500'}`}>
                              {item.oferta.dias_vigencia} días vigencia
                            </p>
                          )}
                          {item.oferta.match_score && (
                            <p className={`text-xs ${getMatchScoreColor(item.oferta.match_score)}`}>
                              Match: {item.oferta.match_score >= 100 ? 'Exacto' : `${item.oferta.match_score}%`}
                            </p>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400 text-sm">Sin oferta</span>
                      )}
                    </td>

                    {/* Prioridad */}
                    <td className="px-4 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getPrioridadColor(item.prioridad)}`}>
                        {(item.prioridad || 'media').toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Leyenda */}
      <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
        <h3 className="font-semibold mb-2">Criterios de selección:</h3>
        <ul className="list-disc list-inside space-y-1">
          <li><strong>Demanda justificada:</strong> Solo productos con ventas en los últimos 90 días</li>
          <li><strong>Prioridad crítica:</strong> Menos de 7 días de cobertura de stock</li>
          <li><strong>Ofertas:</strong> Búsqueda por código exacto o similitud de nombre (60%+ coincidencia)</li>
          <li><strong>Match Exacto:</strong> Producto vinculado directamente con catálogo del proveedor</li>
          <li><strong className="text-orange-600">📈 Ajuste Estacional:</strong> Cantidad aumentada +25% para categorías con alta demanda proyectada el próximo mes</li>
        </ul>
      </div>
    </div>
  );
};

export default PurchaseSuggestions;
