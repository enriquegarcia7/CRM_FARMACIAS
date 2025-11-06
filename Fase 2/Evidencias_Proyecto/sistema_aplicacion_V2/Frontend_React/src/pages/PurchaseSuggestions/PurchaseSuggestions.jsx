import { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Sun,
  Activity,
  TrendingUp,
  Download,
  FileSpreadsheet,
  Upload,
  RefreshCw,
  ShoppingCart,
  Package
} from 'lucide-react';
import { sugerenciasService, ofertasService } from '../../services/api';

const PurchaseSuggestions = () => {
  const [sugerencias, setSugerencias] = useState({
    bajoStock: [],
    estacionales: [],
    epidemiologicas: [],
  });
  const [ofertas, setOfertas] = useState([]);
  const [consolidado, setConsolidado] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingGenerar, setLoadingGenerar] = useState(false);
  const [error, setError] = useState(null);
  const [archivo, setArchivo] = useState(null);

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      setError(null);

      // Llamadas paralelas con timeout de 60 segundos
      const timeoutPromise = (promise, timeout = 60000) => {
        return Promise.race([
          promise,
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Timeout: La solicitud tardó demasiado')), timeout)
          )
        ]);
      };

      const [bajoStockRes, estacionalesRes, epidemiologicasRes, ofertasRes] = await Promise.all([
        timeoutPromise(sugerenciasService.getByLowStock().catch(err => ({ data: [] }))),
        timeoutPromise(sugerenciasService.getBySeason().catch(err => ({ data: [] }))),
        timeoutPromise(sugerenciasService.getByEpidemiological().catch(err => ({ data: [] }))),
        timeoutPromise(ofertasService.getAll().catch(err => ({ data: [] })))
      ]);

      // Función helper para mapear datos de forma segura
      const mapearSugerencia = (item, tipo) => {
        if (!item || !item.producto) return null;

        const baseData = {
          id: item.id,
          producto: item.producto?.descripcion || item.producto?.nombre || 'Producto sin nombre',
          cantidadSugerida: item.cantidad_sugerida || 0,
          proveedor: item.proveedor_recomendado?.nombre || 'Sin proveedor',
          precioUnitario: item.precio_unitario || item.producto?.precio_costo || 0
        };

        if (tipo === 'bajo_stock') {
          return {
            ...baseData,
            stockActual: item.producto?.stock_actual || 0,
            stockMinimo: item.producto?.stock_minimo || 0,
            prioridad: item.prioridad || 'media'
          };
        } else if (tipo === 'estacional') {
          return {
            ...baseData,
            razon: item.razon || 'Temporada actual',
            confianza: item.confianza_ml || 0.75
          };
        } else if (tipo === 'epidemiologico') {
          return {
            ...baseData,
            razon: item.razon || 'Alerta sanitaria',
            fuente: item.fuente_datos || 'MINSAL Chile',
            urgencia: item.prioridad || 'media'
          };
        }
        return baseData;
      };

      // Mapear respuestas del backend de forma segura
      const bajoStock = (bajoStockRes.data || [])
        .map(item => mapearSugerencia(item, 'bajo_stock'))
        .filter(item => item !== null);

      const estacionales = (estacionalesRes.data || [])
        .map(item => mapearSugerencia(item, 'estacional'))
        .filter(item => item !== null);

      const epidemiologicas = (epidemiologicasRes.data || [])
        .map(item => mapearSugerencia(item, 'epidemiologico'))
        .filter(item => item !== null);

      setSugerencias({
        bajoStock,
        estacionales,
        epidemiologicas
      });

      // Mapear ofertas de laboratorios de forma segura
      const ofertasMapeadas = (ofertasRes.data || [])
        .map(oferta => {
          if (!oferta) return null;
          return {
            id: oferta.id,
            laboratorio: oferta.laboratorio?.nombre || oferta.proveedor?.nombre || 'Laboratorio',
            producto: oferta.producto_catalogo?.descripcion || oferta.producto_catalogo?.nombre || 'Producto',
            descuento: `${oferta.descuento || 0}%`,
            precioNormal: oferta.precio_normal || 0,
            precioOferta: oferta.precio_oferta || 0,
            vigencia: oferta.fecha_fin || oferta.fecha_vigencia
          };
        })
        .filter(oferta => oferta !== null);

      setOfertas(ofertasMapeadas);

      // Cargar consolidado de compras (con timeout)
      await timeoutPromise(cargarConsolidado(), 30000).catch(err => {
        console.warn('Error cargando consolidado:', err);
      });

    } catch (error) {
      console.error('Error cargando sugerencias:', error);
      const errorMessage = error.message === 'Timeout: La solicitud tardó demasiado'
        ? 'La carga está tardando más de lo esperado. Por favor, intenta generar sugerencias primero.'
        : (error.response?.data?.message || error.message || 'Error al cargar sugerencias de compra');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const cargarConsolidado = async () => {
    try {
      const response = await sugerenciasService.consolidar();

      // Verificar que la respuesta tenga datos válidos
      if (response.data && response.data.consolidado) {
        setConsolidado(response.data.consolidado);
      } else {
        setConsolidado(null);
      }
    } catch (error) {
      console.warn('No se pudo cargar el consolidado:', error);
      setConsolidado(null);
    }
  };

  const generarSugerencias = async () => {
    try {
      setLoadingGenerar(true);
      const response = await sugerenciasService.generar({
        limite: 100,
        forzar_mapeo: true
      });

      if (response.data.success) {
        alert(`
✅ Sugerencias generadas exitosamente

📊 Estadísticas:
- Productos críticos evaluados: ${response.data.estadisticas.total_criticos}
- Sugerencias creadas: ${response.data.estadisticas.sugerencias_creadas}
- Productos sin mapeo: ${response.data.estadisticas.productos_sin_mapeo}
- Productos sin proveedor: ${response.data.estadisticas.productos_sin_proveedor}
        `);

        // Recargar datos
        await cargarDatos();
      }
    } catch (error) {
      console.error('Error generando sugerencias:', error);
      alert('Error al generar sugerencias: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoadingGenerar(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
    }).format(value);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-CL');
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (file) {
      setArchivo(file);
      // Aquí se procesará el archivo Excel/PDF con ETL
      alert(`Archivo "${file.name}" cargado. Procesando ofertas de laboratorios...`);
      // Implementar lógica de ETL
    }
  };

  const descargarExcelProveedor = async (nombreProveedor) => {
    try {
      const response = await sugerenciasService.exportExcel({
        proveedor: nombreProveedor
      });

      // Crear un enlace de descarga
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `orden_compra_${nombreProveedor}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      alert(`✅ Orden de compra para ${nombreProveedor} descargada exitosamente`);
    } catch (error) {
      console.error('Error descargando Excel:', error);
      alert('Error al generar Excel: ' + (error.response?.data?.message || error.message));
    }
  };

  const generarOrdenCompra = (sugerencias) => {
    alert(`Generando orden de compra para ${sugerencias.length} productos...`);
    // Implementar lógica de generación de orden de compra
  };

  const getPrioridadColor = (prioridad) => {
    switch (prioridad) {
      case 'alta': return 'bg-red-100 text-red-800';
      case 'media': return 'bg-yellow-100 text-yellow-800';
      case 'baja': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-4 text-xl text-gray-600">Cargando sugerencias...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="bg-red-50 border border-red-200 rounded-lg p-8 max-w-md">
          <div className="flex items-center mb-4">
            <svg className="w-8 h-8 text-red-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-lg font-semibold text-red-800">Error al cargar sugerencias</h3>
          </div>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={cargarDatos}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Sugerencias de Compra Inteligente</h1>
        <div className="flex gap-3">
          <button
            onClick={generarSugerencias}
            disabled={loadingGenerar}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg transition-colors"
          >
            {loadingGenerar ? (
              <>
                <RefreshCw size={20} className="animate-spin" />
                Generando...
              </>
            ) : (
              <>
                <RefreshCw size={20} />
                Generar Sugerencias
              </>
            )}
          </button>
          <button
            onClick={() => generarOrdenCompra([...sugerencias.bajoStock, ...sugerencias.estacionales, ...sugerencias.epidemiologicas])}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Download size={20} />
            Generar Orden de Compra
          </button>
        </div>
      </div>

      {/* Tarjetas de resumen */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-red-50 border-l-4 border-red-500 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-red-800 font-semibold">Bajo Stock</p>
              <p className="text-3xl font-bold text-red-900 mt-2">
                {sugerencias.bajoStock.length}
              </p>
              <p className="text-sm text-red-700 mt-1">productos críticos</p>
            </div>
            <AlertTriangle size={40} className="text-red-500" />
          </div>
        </div>

        <div className="bg-orange-50 border-l-4 border-orange-500 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-800 font-semibold">Estacionales</p>
              <p className="text-3xl font-bold text-orange-900 mt-2">
                {sugerencias.estacionales.length}
              </p>
              <p className="text-sm text-orange-700 mt-1">por temporada (ML)</p>
            </div>
            <Sun size={40} className="text-orange-500" />
          </div>
        </div>

        <div className="bg-blue-50 border-l-4 border-blue-500 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-800 font-semibold">Epidemiológicas</p>
              <p className="text-3xl font-bold text-blue-900 mt-2">
                {sugerencias.epidemiologicas.length}
              </p>
              <p className="text-sm text-blue-700 mt-1">según MINSAL</p>
            </div>
            <Activity size={40} className="text-blue-500" />
          </div>
        </div>
      </div>

      {/* Carga de ofertas de laboratorios */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FileSpreadsheet size={24} className="text-blue-600" />
            <h2 className="text-xl font-semibold">Ofertas de Laboratorios (ETL)</h2>
          </div>
          <label className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg cursor-pointer transition-colors">
            <Upload size={20} />
            Cargar Excel/PDF
            <input
              type="file"
              accept=".xlsx,.xls,.pdf"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          El sistema procesará automáticamente las ofertas cada 3 días. Última actualización: Hace 2 días
        </p>

        {ofertas.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Laboratorio</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Producto</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Descuento</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Precio Normal</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Precio Oferta</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Vigencia</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {ofertas.map((oferta) => (
                  <tr key={oferta.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{oferta.laboratorio}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{oferta.producto}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-semibold">
                        {oferta.descuento}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 line-through">{formatCurrency(oferta.precioNormal)}</td>
                    <td className="px-4 py-3 text-sm font-bold text-green-600">{formatCurrency(oferta.precioOferta)}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{formatDate(oferta.vigencia)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Órdenes de Compra Consolidadas por Proveedor */}
      {consolidado && Object.keys(consolidado).length > 0 && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg shadow-lg p-6 border-2 border-purple-200">
          <div className="flex items-center gap-3 mb-6">
            <ShoppingCart size={28} className="text-purple-600" />
            <div>
              <h2 className="text-2xl font-bold text-purple-900">Órdenes de Compra Optimizadas</h2>
              <p className="text-sm text-purple-700">Sugerencias agrupadas por proveedor con selección automática del mejor precio</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(consolidado).map(([proveedorNombre, data]) => (
              <div key={proveedorNombre} className="bg-white rounded-lg shadow-md border-2 border-gray-200 overflow-hidden">
                <div className={`p-4 ${data.cumple_minimo ? 'bg-green-50' : 'bg-red-50'}`}>
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">{proveedorNombre}</h3>
                      <p className="text-sm text-gray-600">{data.sugerencias.length} productos sugeridos</p>
                    </div>
                    <Package size={24} className="text-gray-600" />
                  </div>

                  <div className="mt-3 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-700">Total:</span>
                      <span className="text-2xl font-bold text-gray-900">{formatCurrency(data.total)}</span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-700">Mínimo requerido:</span>
                      <span className="text-sm font-semibold text-gray-600">{formatCurrency(data.minimo_requerido)}</span>
                    </div>

                    {data.cumple_minimo ? (
                      <div className="flex items-center gap-2 bg-green-100 text-green-800 px-3 py-2 rounded-md">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <span className="text-sm font-semibold">Cumple mínimo de pedido</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 bg-red-100 text-red-800 px-3 py-2 rounded-md">
                        <AlertTriangle size={18} />
                        <span className="text-sm font-semibold">No cumple mínimo - Falta {formatCurrency(data.minimo_requerido - data.total)}</span>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => descargarExcelProveedor(proveedorNombre)}
                    className="mt-4 w-full flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    <Download size={18} />
                    Descargar Orden Excel
                  </button>
                </div>

                <div className="p-4 max-h-96 overflow-y-auto">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Productos incluidos:</h4>
                  <div className="space-y-2">
                    {data.sugerencias.slice(0, 10).map((sug, idx) => (
                      <div key={idx} className="flex justify-between items-start text-sm border-b border-gray-100 pb-2">
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">{sug.producto?.nombre || 'Producto'}</p>
                          <p className="text-xs text-gray-500">
                            Cantidad: {sug.cantidad_sugerida} × {formatCurrency(sug.precio_unitario)}
                            {sug.tiene_oferta && (
                              <span className="ml-2 bg-green-100 text-green-800 px-2 py-0.5 rounded text-xs font-semibold">
                                ¡OFERTA! -{sug.descuento_porcentaje}%
                              </span>
                            )}
                          </p>
                        </div>
                        <p className="font-semibold text-gray-900">{formatCurrency(sug.total)}</p>
                      </div>
                    ))}
                    {data.sugerencias.length > 10 && (
                      <p className="text-xs text-gray-500 italic">... y {data.sugerencias.length - 10} productos más</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mensaje informativo si no hay sugerencias */}
      {sugerencias.bajoStock.length === 0 && sugerencias.estacionales.length === 0 && sugerencias.epidemiologicas.length === 0 && (
        <div className="bg-blue-50 border-l-4 border-blue-500 rounded-lg p-6 mb-6">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-6 w-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-lg font-semibold text-blue-900">No hay sugerencias generadas</h3>
              <p className="text-sm text-blue-800 mt-2">
                Para comenzar, haz clic en el botón <strong>"Generar Sugerencias"</strong> para analizar tu inventario
                y crear recomendaciones inteligentes de compra basadas en:
              </p>
              <ul className="list-disc list-inside text-sm text-blue-800 mt-2 space-y-1">
                <li>Stock crítico y bajo stock</li>
                <li>Patrones estacionales (Machine Learning)</li>
                <li>Alertas epidemiológicas</li>
                <li>Optimización de precios por proveedor</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Sugerencias por Bajo Stock */}
      {sugerencias.bajoStock.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <AlertTriangle size={24} className="text-red-600" />
              <h2 className="text-xl font-semibold">Sugerencias por Bajo Stock</h2>
            </div>
            <p className="text-sm text-gray-600 mt-1">Productos que requieren reposición urgente</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Producto</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock Actual</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock Mínimo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cant. Sugerida</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Proveedor</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Precio Unit.</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Prioridad</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sugerencias.bajoStock.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{item.producto}</td>
                  <td className="px-6 py-4 text-sm text-red-600 font-semibold">{item.stockActual}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{item.stockMinimo}</td>
                  <td className="px-6 py-4 text-sm font-semibold text-blue-600">{item.cantidadSugerida}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{item.proveedor}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{formatCurrency(item.precioUnitario)}</td>
                  <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                    {formatCurrency(item.cantidadSugerida * item.precioUnitario)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getPrioridadColor(item.prioridad)}`}>
                      {item.prioridad.toUpperCase()}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      )}

      {/* Sugerencias Estacionales (ML) */}
      {sugerencias.estacionales.length > 0 && (
        <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Sun size={24} className="text-orange-600" />
            <h2 className="text-xl font-semibold">Sugerencias Estacionales (Machine Learning)</h2>
          </div>
          <p className="text-sm text-gray-600 mt-1">Predicciones basadas en patrones históricos y estación del año</p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Producto</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Razón</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cant. Sugerida</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Proveedor</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Precio Unit.</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confianza</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sugerencias.estacionales.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{item.producto}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{item.razon}</td>
                  <td className="px-6 py-4 text-sm font-semibold text-blue-600">{item.cantidadSugerida}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{item.proveedor}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{formatCurrency(item.precioUnitario)}</td>
                  <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                    {formatCurrency(item.cantidadSugerida * item.precioUnitario)}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <div className="flex items-center">
                      <TrendingUp size={16} className="text-green-600 mr-1" />
                      <span className="font-semibold text-green-600">{(item.confianza * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      )}

      {/* Sugerencias Epidemiológicas (MINSAL) */}
      {sugerencias.epidemiologicas.length > 0 && (
        <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Activity size={24} className="text-blue-600" />
            <h2 className="text-xl font-semibold">Sugerencias Epidemiológicas (MINSAL)</h2>
          </div>
          <p className="text-sm text-gray-600 mt-1">Basadas en alertas sanitarias y tendencias epidemiológicas actuales</p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Producto</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Razón / Alerta</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fuente</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cant. Sugerida</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Proveedor</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Precio Unit.</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Urgencia</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sugerencias.epidemiologicas.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{item.producto}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{item.razon}</td>
                  <td className="px-6 py-4 text-sm">
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-semibold">
                      {item.fuente}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm font-semibold text-blue-600">{item.cantidadSugerida}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{item.proveedor}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{formatCurrency(item.precioUnitario)}</td>
                  <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                    {formatCurrency(item.cantidadSugerida * item.precioUnitario)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getPrioridadColor(item.urgencia)}`}>
                      {item.urgencia.toUpperCase()}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      )}
    </div>
  );
};

export default PurchaseSuggestions;
