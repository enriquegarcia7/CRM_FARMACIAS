import { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Sun,
  Activity,
  TrendingUp,
  Download,
  FileSpreadsheet,
  Upload
} from 'lucide-react';
import { sugerenciasService, ofertasService } from '../../services/api';

const PurchaseSuggestions = () => {
  const [sugerencias, setSugerencias] = useState({
    bajoStock: [],
    estacionales: [],
    epidemiologicas: [],
  });
  const [ofertas, setOfertas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [archivo, setArchivo] = useState(null);

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      setError(null);

      // Llamadas paralelas a los 4 endpoints del backend
      const [bajoStockRes, estacionalesRes, epidemiologicasRes, ofertasRes] = await Promise.all([
        sugerenciasService.getByLowStock(),
        sugerenciasService.getBySeason(),
        sugerenciasService.getByEpidemiological(),
        ofertasService.getActive()
      ]);

      // Mapear respuestas del backend al formato esperado por el frontend
      setSugerencias({
        bajoStock: bajoStockRes.data.map(item => ({
          id: item.id,
          producto: item.producto?.descripcion || item.producto?.nombre || 'Producto sin nombre',
          stockActual: item.producto?.stock_actual || 0,
          stockMinimo: item.producto?.stock_minimo || 0,
          cantidadSugerida: item.cantidad_sugerida,
          proveedor: item.proveedor?.nombre || 'Sin proveedor',
          precioUnitario: item.producto?.precio_costo || 0,
          prioridad: item.prioridad || 'media'
        })),
        estacionales: estacionalesRes.data.map(item => ({
          id: item.id,
          producto: item.producto?.descripcion || item.producto?.nombre || 'Producto sin nombre',
          razon: item.razon || 'Temporada actual',
          cantidadSugerida: item.cantidad_sugerida,
          proveedor: item.proveedor?.nombre || 'Sin proveedor',
          precioUnitario: item.producto?.precio_costo || 0,
          confianza: item.confianza || 0.75
        })),
        epidemiologicas: epidemiologicasRes.data.map(item => ({
          id: item.id,
          producto: item.producto?.descripcion || item.producto?.nombre || 'Producto sin nombre',
          razon: item.razon || 'Alerta sanitaria',
          fuente: item.fuente || 'MINSAL Chile',
          cantidadSugerida: item.cantidad_sugerida,
          proveedor: item.proveedor?.nombre || 'Sin proveedor',
          precioUnitario: item.producto?.precio_costo || 0,
          urgencia: item.prioridad || 'media'
        }))
      });

      // Mapear ofertas de laboratorios
      setOfertas(ofertasRes.data.map(oferta => ({
        id: oferta.id,
        laboratorio: oferta.proveedor?.nombre || 'Laboratorio',
        producto: oferta.producto?.descripcion || oferta.producto?.nombre || 'Producto',
        descuento: `${oferta.descuento_porcentaje}%`,
        precioNormal: oferta.precio_normal,
        precioOferta: oferta.precio_oferta,
        vigencia: oferta.fecha_vigencia
      })));

    } catch (error) {
      console.error('Error cargando sugerencias:', error);
      setError(error.response?.data?.message || error.message || 'Error al cargar sugerencias de compra');
    } finally {
      setLoading(false);
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
        <button
          onClick={() => generarOrdenCompra([...sugerencias.bajoStock, ...sugerencias.estacionales, ...sugerencias.epidemiologicas])}
          className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          <Download size={20} />
          Generar Orden de Compra
        </button>
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

      {/* Sugerencias por Bajo Stock */}
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

      {/* Sugerencias Estacionales (ML) */}
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

      {/* Sugerencias Epidemiológicas (MINSAL) */}
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
    </div>
  );
};

export default PurchaseSuggestions;
