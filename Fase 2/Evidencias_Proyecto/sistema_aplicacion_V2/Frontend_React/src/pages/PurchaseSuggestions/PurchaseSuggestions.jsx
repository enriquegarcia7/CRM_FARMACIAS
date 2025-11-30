import { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  Sun,
  Activity,
  TrendingUp,
  Download,
  RefreshCw,
  ShoppingCart,
  Package,
  ChevronLeft,
  ChevronRight,
  Filter
} from 'lucide-react';
import { sugerenciasService } from '../../services/api';

// Skeleton para carga
const SkeletonRow = () => (
  <tr className="animate-pulse">
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
  const [sugerencias, setSugerencias] = useState([]);
  const [conteos, setConteos] = useState({ bajo_stock: 0, estacional: 0, epidemiologico: 0, total: 0 });
  const [pagination, setPagination] = useState({ page: 1, page_size: 50, total_items: 0, total_pages: 0 });
  const [activeTab, setActiveTab] = useState('bajo_stock');
  const [loading, setLoading] = useState(true);
  const [loadingGenerar, setLoadingGenerar] = useState(false);
  const [error, setError] = useState(null);
  const [consolidado, setConsolidado] = useState(null);

  const cargarSugerencias = useCallback(async (tipo = activeTab, page = 1) => {
    try {
      setLoading(true);
      setError(null);

      const response = await sugerenciasService.getTodas({
        tipo: tipo,
        page: page,
        page_size: 50
      });

      setSugerencias(response.data.results || []);
      setConteos(response.data.conteos || { bajo_stock: 0, estacional: 0, epidemiologico: 0, total: 0 });
      setPagination(response.data.pagination || { page: 1, page_size: 50, total_items: 0, total_pages: 0 });

    } catch (err) {
      console.error('Error cargando sugerencias:', err);
      setError(err.response?.data?.message || err.message || 'Error al cargar sugerencias');
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    cargarSugerencias(activeTab, 1);
  }, [activeTab]);

  const cargarConsolidado = async () => {
    try {
      const response = await sugerenciasService.consolidar();
      if (response.data?.consolidado) {
        setConsolidado(response.data.consolidado);
      }
    } catch (err) {
      console.warn('No se pudo cargar consolidado:', err);
    }
  };

  const generarSugerencias = async () => {
    try {
      setLoadingGenerar(true);
      const response = await sugerenciasService.generar({ limite: 100, forzar_mapeo: true });

      if (response.data.success) {
        alert(`✅ Sugerencias generadas exitosamente\n\n📊 Estadísticas:\n- Productos críticos: ${response.data.estadisticas.total_criticos}\n- Sugerencias creadas: ${response.data.estadisticas.sugerencias_creadas}`);
        await cargarSugerencias(activeTab, 1);
        await cargarConsolidado();
      }
    } catch (err) {
      console.error('Error generando sugerencias:', err);
      alert('Error al generar sugerencias: ' + (err.response?.data?.message || err.message));
    } finally {
      setLoadingGenerar(false);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.total_pages) {
      cargarSugerencias(activeTab, newPage);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(value || 0);
  };

  const getPrioridadColor = (prioridad) => {
    switch (prioridad) {
      case 'alta': return 'bg-red-100 text-red-800';
      case 'media': return 'bg-yellow-100 text-yellow-800';
      case 'baja': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const tabs = [
    { id: 'bajo_stock', label: 'Bajo Stock', icon: AlertTriangle, color: 'red', count: conteos.bajo_stock },
    { id: 'estacional', label: 'Estacionales', icon: Sun, color: 'orange', count: conteos.estacional },
    { id: 'epidemiologico', label: 'Epidemiológicas', icon: Activity, color: 'blue', count: conteos.epidemiologico },
  ];

  const descargarExcelProveedor = async (nombreProveedor) => {
    try {
      const response = await sugerenciasService.exportExcel({ proveedor: nombreProveedor });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `orden_compra_${nombreProveedor}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Error al generar Excel: ' + (err.response?.data?.message || err.message));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Sugerencias de Compra</h1>
        <div className="flex gap-3">
          <button
            onClick={generarSugerencias}
            disabled={loadingGenerar}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg transition-colors"
          >
            {loadingGenerar ? (
              <><RefreshCw size={20} className="animate-spin" /> Generando...</>
            ) : (
              <><RefreshCw size={20} /> Generar Sugerencias</>
            )}
          </button>
          <button
            onClick={cargarConsolidado}
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <ShoppingCart size={20} /> Ver Consolidado
          </button>
        </div>
      </div>

      {/* Tarjetas de resumen con conteos */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {loading ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : (
          tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            const colorClasses = {
              red: { bg: 'bg-red-50', border: 'border-red-500', text: 'text-red-800', count: 'text-red-900', icon: 'text-red-500' },
              orange: { bg: 'bg-orange-50', border: 'border-orange-500', text: 'text-orange-800', count: 'text-orange-900', icon: 'text-orange-500' },
              blue: { bg: 'bg-blue-50', border: 'border-blue-500', text: 'text-blue-800', count: 'text-blue-900', icon: 'text-blue-500' },
            }[tab.color];

            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`${colorClasses.bg} border-l-4 ${colorClasses.border} rounded-lg shadow p-6 text-left transition-all hover:shadow-lg ${isActive ? 'ring-2 ring-offset-2 ring-' + tab.color + '-500' : ''}`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className={`${colorClasses.text} font-semibold`}>{tab.label}</p>
                    <p className={`text-3xl font-bold ${colorClasses.count} mt-2`}>{tab.count}</p>
                    <p className={`text-sm ${colorClasses.text} mt-1`}>
                      {isActive ? 'Mostrando' : 'Click para ver'}
                    </p>
                  </div>
                  <Icon size={40} className={colorClasses.icon} />
                </div>
              </button>
            );
          })
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="text-red-500" />
          <span className="text-red-700">{error}</span>
          <button onClick={() => cargarSugerencias(activeTab, 1)} className="ml-auto text-red-600 hover:text-red-800 font-medium">
            Reintentar
          </button>
        </div>
      )}

      {/* Tabla de sugerencias */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {tabs.find(t => t.id === activeTab)?.icon && (
              <div className={`text-${tabs.find(t => t.id === activeTab)?.color}-600`}>
                {(() => { const Icon = tabs.find(t => t.id === activeTab)?.icon; return <Icon size={24} />; })()}
              </div>
            )}
            <h2 className="text-xl font-semibold">
              {tabs.find(t => t.id === activeTab)?.label}
            </h2>
            <span className="text-sm text-gray-500 ml-2">
              ({pagination.total_items} sugerencias)
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span>Página {pagination.page} de {pagination.total_pages || 1}</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Producto</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock Actual</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cant. Sugerida</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Proveedor</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Precio Unit.</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {activeTab === 'estacional' ? 'Confianza' : 'Prioridad'}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                [...Array(10)].map((_, i) => <SkeletonRow key={i} />)
              ) : sugerencias.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center text-gray-500">
                    <div className="flex flex-col items-center gap-3">
                      <Filter size={48} className="text-gray-300" />
                      <p className="text-lg font-medium">No hay sugerencias en esta categoría</p>
                      <p className="text-sm">Haz clic en "Generar Sugerencias" para analizar tu inventario</p>
                    </div>
                  </td>
                </tr>
              ) : (
                sugerencias.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {item.producto?.nombre || item.producto?.descripcion || 'Sin nombre'}
                        </p>
                        <p className="text-xs text-gray-500">{item.producto?.codigo}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-red-600 font-semibold">
                      {item.producto?.stock_actual || 0}
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold text-blue-600">
                      {item.cantidad_sugerida}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {item.proveedor_recomendado?.nombre || 'Sin proveedor'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {formatCurrency(item.precio_unitario)}
                      {item.tiene_oferta && (
                        <span className="ml-2 bg-green-100 text-green-800 px-2 py-0.5 rounded text-xs">
                          -{item.descuento_porcentaje}%
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                      {formatCurrency(item.cantidad_sugerida * (item.precio_unitario || 0))}
                    </td>
                    <td className="px-6 py-4">
                      {activeTab === 'estacional' ? (
                        <div className="flex items-center">
                          <TrendingUp size={16} className="text-green-600 mr-1" />
                          <span className="font-semibold text-green-600">
                            {((item.confianza_ml || 0) * 100).toFixed(0)}%
                          </span>
                        </div>
                      ) : (
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getPrioridadColor(item.prioridad)}`}>
                          {(item.prioridad || 'media').toUpperCase()}
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Paginación */}
        {pagination.total_pages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between bg-gray-50">
            <div className="text-sm text-gray-600">
              Mostrando {((pagination.page - 1) * pagination.page_size) + 1} - {Math.min(pagination.page * pagination.page_size, pagination.total_items)} de {pagination.total_items}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handlePageChange(pagination.page - 1)}
                disabled={!pagination.has_previous}
                className="p-2 rounded-lg border border-gray-300 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft size={20} />
              </button>

              {/* Números de página */}
              <div className="flex gap-1">
                {[...Array(Math.min(5, pagination.total_pages))].map((_, i) => {
                  let pageNum;
                  if (pagination.total_pages <= 5) {
                    pageNum = i + 1;
                  } else if (pagination.page <= 3) {
                    pageNum = i + 1;
                  } else if (pagination.page >= pagination.total_pages - 2) {
                    pageNum = pagination.total_pages - 4 + i;
                  } else {
                    pageNum = pagination.page - 2 + i;
                  }

                  return (
                    <button
                      key={pageNum}
                      onClick={() => handlePageChange(pageNum)}
                      className={`px-3 py-1 rounded-lg text-sm font-medium ${
                        pagination.page === pageNum
                          ? 'bg-blue-600 text-white'
                          : 'border border-gray-300 hover:bg-gray-100'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => handlePageChange(pagination.page + 1)}
                disabled={!pagination.has_next}
                className="p-2 rounded-lg border border-gray-300 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight size={20} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Consolidado por proveedor */}
      {consolidado && Object.keys(consolidado).length > 0 && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg shadow-lg p-6 border-2 border-purple-200">
          <div className="flex items-center gap-3 mb-6">
            <ShoppingCart size={28} className="text-purple-600" />
            <div>
              <h2 className="text-2xl font-bold text-purple-900">Órdenes de Compra Consolidadas</h2>
              <p className="text-sm text-purple-700">Agrupadas por proveedor con selección del mejor precio</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(consolidado).map(([proveedorNombre, data]) => (
              <div key={proveedorNombre} className="bg-white rounded-lg shadow-md border overflow-hidden">
                <div className={`p-4 ${data.cumple_minimo ? 'bg-green-50' : 'bg-red-50'}`}>
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="text-lg font-bold text-gray-900">{proveedorNombre}</h3>
                      <p className="text-sm text-gray-600">{data.sugerencias?.length || 0} productos</p>
                    </div>
                    <Package size={20} className="text-gray-500" />
                  </div>

                  <div className="mt-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-gray-600">Total:</span>
                      <span className="text-xl font-bold">{formatCurrency(data.total)}</span>
                    </div>
                    {data.cumple_minimo ? (
                      <div className="text-green-700 text-sm font-medium">✓ Cumple mínimo</div>
                    ) : (
                      <div className="text-red-700 text-sm font-medium">
                        ⚠ Falta {formatCurrency(data.minimo_requerido - data.total)}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => descargarExcelProveedor(proveedorNombre)}
                    className="mt-3 w-full flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded-lg text-sm transition-colors"
                  >
                    <Download size={16} /> Descargar Excel
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PurchaseSuggestions;
