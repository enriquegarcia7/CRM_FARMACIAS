import { useState, useEffect, useRef } from 'react';
import { Search, AlertTriangle, Package, Filter, Upload, X, ChevronLeft, ChevronRight, Clock, ChevronUp, ChevronDown } from 'lucide-react';
import { productosService } from '../../services/api';

const Inventory = () => {
  const [productos, setProductos] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchInput, setSearchInput] = useState(''); // Para debounce
  const [filtroStock, setFiltroStock] = useState(''); // '', 'bajo', 'normal'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ultimaCarga, setUltimaCarga] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'codigo', direction: 'asc' });

  // Paginación backend
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 50;

  // Modal de carga Excel
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  // Cargar productos cuando cambian filtros, página u ordenamiento
  useEffect(() => {
    cargarProductos();
    cargarUltimaCarga();
  }, [currentPage, filtroStock, searchTerm, sortConfig]);

  // Debounce para búsqueda (500ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchTerm(searchInput);
      setCurrentPage(1);
    }, 500);

    return () => clearTimeout(timer);
  }, [searchInput]);

  const cargarProductos = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: currentPage,
        page_size: itemsPerPage
      };

      if (filtroStock) params.filtro_stock = filtroStock;
      if (searchTerm) params.search = searchTerm;

      // Agregar ordenamiento
      params.ordering = sortConfig.direction === 'desc' ? `-${sortConfig.key}` : sortConfig.key;

      const response = await productosService.getAll(params);

      setProductos(response.data.results || []);
      setTotalItems(response.data.count || 0);
      setTotalPages(Math.ceil((response.data.count || 0) / itemsPerPage));

    } catch (error) {
      console.error('Error cargando productos:', error);
      setError(error.response?.data?.message || error.message || 'Error al cargar inventario');
    } finally {
      setLoading(false);
    }
  };

  const cargarUltimaCarga = async () => {
    try {
      const response = await productosService.getUltimaCarga();
      if (response.data.fecha_ultima_carga) {
        setUltimaCarga(new Date(response.data.fecha_ultima_carga));
      }
    } catch (error) {
      console.error('Error cargando fecha de última carga:', error);
    }
  };

  const formatearFechaHora = (fecha) => {
    if (!fecha) return 'No disponible';

    const opciones = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    };

    return fecha.toLocaleString('es-CL', opciones);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validar extensión
      if (!file.name.match(/\.(xlsx|xls)$/i)) {
        alert('Por favor selecciona un archivo Excel (.xlsx o .xls)');
        return;
      }
      setUploadFile(file);
      setUploadResult(null);
      setShowConfirmation(true); // Mostrar confirmación
    }
  };

  const handleUploadExcel = async () => {
    if (!uploadFile) {
      alert('Por favor selecciona un archivo');
      return;
    }

    try {
      setUploading(true);
      setUploadResult(null);
      setUploadProgress(0);

      // Simular progreso mientras se procesa el archivo
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) return prev;
          return prev + Math.random() * 15;
        });
      }, 300);

      const formData = new FormData();
      formData.append('archivo', uploadFile);

      const response = await productosService.cargarExcel(formData);

      // Completar la barra de progreso
      clearInterval(progressInterval);
      setUploadProgress(100);

      setUploadResult({
        success: true,
        ...response.data
      });

      // Recargar productos y fecha de última carga después de cargar Excel
      setTimeout(() => {
        cargarProductos();
        cargarUltimaCarga();
      }, 1000);

    } catch (error) {
      console.error('Error cargando Excel:', error);
      setUploadProgress(0);
      setUploadResult({
        success: false,
        error: error.response?.data?.error || error.message || 'Error al cargar archivo'
      });
    } finally {
      setUploading(false);
    }
  };

  const closeUploadModal = () => {
    setShowUploadModal(false);
    setUploadFile(null);
    setUploadResult(null);
    setShowConfirmation(false);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getStockStatus = (producto) => {
    // Usar stock_minimo de la BD para consistencia con el filtro del backend
    const stockMinimo = producto.stock_minimo || 5;
    const porcentaje = stockMinimo > 0 ? (producto.stock_actual / stockMinimo) * 100 : 100;
    if (porcentaje < 50) return { color: 'text-red-600 bg-red-100', label: 'Crítico' };
    if (porcentaje < 100) return { color: 'text-yellow-600 bg-yellow-100', label: 'Bajo' };
    return { color: 'text-green-600 bg-green-100', label: 'Normal' };
  };

  const nextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const prevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const indexOfFirstItem = (currentPage - 1) * itemsPerPage + 1;
  const indexOfLastItem = Math.min(currentPage * itemsPerPage, totalItems);

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
    setCurrentPage(1);
  };

  const SortIcon = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) {
      return <ChevronUp size={14} className="text-gray-300" />;
    }
    return sortConfig.direction === 'asc'
      ? <ChevronUp size={14} className="text-blue-600" />
      : <ChevronDown size={14} className="text-blue-600" />;
  };

  if (loading && productos.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-4 text-xl text-gray-600">Cargando inventario...</span>
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
            <h3 className="text-lg font-semibold text-red-800">Error al cargar inventario</h3>
          </div>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={cargarProductos}
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
        <h1 className="text-3xl font-bold text-gray-800">Inventario de Productos</h1>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            <Upload size={20} className="mr-2" />
            Cargar Excel
          </button>
          <div className="flex items-center bg-blue-100 text-blue-700 px-4 py-2 rounded-lg">
            <Package size={20} className="mr-2" />
            <span className="font-semibold">
              {totalItems.toLocaleString('es-CL')} productos
            </span>
          </div>
        </div>
      </div>

      {/* Fecha de última actualización */}
      {ultimaCarga && (
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-4 shadow-sm">
          <div className="flex items-center">
            <Clock size={20} className="text-indigo-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-indigo-900">Última actualización de stock</p>
              <p className="text-lg font-bold text-indigo-700">{formatearFechaHora(ultimaCarga)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Filtros y búsqueda */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Buscar por código o nombre de producto..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={20} className="text-gray-400" />
            <select
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={filtroStock}
              onChange={(e) => {
                setFiltroStock(e.target.value);
                setCurrentPage(1);
              }}
            >
              <option value="">Todos los productos</option>
              <option value="bajo">Bajo stock</option>
              <option value="normal">Stock normal</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tabla de productos */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading && (
          <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th onClick={() => handleSort('codigo')} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-28 cursor-pointer hover:bg-gray-100 select-none">
                  <div className="flex items-center gap-1">Código <SortIcon columnKey="codigo" /></div>
                </th>
                <th onClick={() => handleSort('descripcion')} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none">
                  <div className="flex items-center gap-1">Producto <SortIcon columnKey="descripcion" /></div>
                </th>
                <th onClick={() => handleSort('stock_actual')} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24 cursor-pointer hover:bg-gray-100 select-none">
                  <div className="flex items-center gap-1">Stock <SortIcon columnKey="stock_actual" /></div>
                </th>
                <th onClick={() => handleSort('stock_minimo')} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24 cursor-pointer hover:bg-gray-100 select-none">
                  <div className="flex items-center gap-1">Stock Mín. ML <SortIcon columnKey="stock_minimo" /></div>
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                  Demanda Diaria
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                  Precio Venta
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                  Estado
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {productos.map((producto) => {
                const status = getStockStatus(producto);
                return (
                  <tr key={producto.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                      {producto.codigo}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {producto.nombre || producto.descripcion}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-semibold text-gray-900">
                      {producto.stock_actual}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      <div className="flex flex-col">
                        <span className="font-bold text-indigo-600">
                          {producto.stock_minimo_calculado || producto.stock_minimo || 5}
                        </span>
                        {producto.stock_minimo_calculado && (
                          <span className="text-xs text-indigo-400 font-medium">
                            ML + Histórico
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      {producto.metricas_stock ? (
                        <div className="flex flex-col">
                          <span className="font-medium">
                            {producto.metricas_stock.demanda_promedio_diaria?.toFixed(1) || '0.0'} u/día
                          </span>
                          <span className="text-xs text-gray-500">
                            {Math.round(producto.metricas_stock.dias_cobertura || 0)} días cobertura
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-400">Sin datos</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                      ${parseFloat(producto.precio_venta || 0).toLocaleString('es-CL')}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold ${status.color}`}
                      >
                        {status.label}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {productos.length === 0 && !loading && (
          <div className="text-center py-12 text-gray-500">
            No se encontraron productos
          </div>
        )}

        {/* Controles de paginación */}
        {productos.length > 0 && (
          <div className="bg-gray-50 px-4 py-3 flex items-center justify-between border-t border-gray-200">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={prevPage}
                disabled={currentPage === 1 || loading}
                className={`relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md ${
                  currentPage === 1 || loading
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                Anterior
              </button>
              <button
                onClick={nextPage}
                disabled={currentPage === totalPages || loading}
                className={`ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md ${
                  currentPage === totalPages || loading
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                Siguiente
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Mostrando <span className="font-medium">{indexOfFirstItem}</span> a{' '}
                  <span className="font-medium">{indexOfLastItem}</span> de{' '}
                  <span className="font-medium">{totalItems.toLocaleString('es-CL')}</span> resultados
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <button
                    onClick={prevPage}
                    disabled={currentPage === 1 || loading}
                    className={`relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 text-sm font-medium ${
                      currentPage === 1 || loading
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-white text-gray-500 hover:bg-gray-50'
                    }`}
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                  <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                    Página {currentPage} de {totalPages}
                  </span>
                  <button
                    onClick={nextPage}
                    disabled={currentPage === totalPages || loading}
                    className={`relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 text-sm font-medium ${
                      currentPage === totalPages || loading
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-white text-gray-500 hover:bg-gray-50'
                    }`}
                  >
                    <ChevronRight className="h-5 w-5" />
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modal de carga de Excel */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-gray-800">Cargar Excel de Inventario</h3>
              <button
                onClick={closeUploadModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={24} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Seleccionar archivo Excel (.xlsx, .xls)
                </label>
                <p className="text-xs text-gray-500 mb-2">
                  Columnas requeridas: CODIGO, PRODUCTO, PREC UNITARIO, PREC UNIDADES, STOCK
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={handleFileSelect}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              </div>

              {uploadFile && showConfirmation && !uploadResult && (
                <div className="bg-yellow-50 border-2 border-yellow-300 rounded-lg p-4">
                  <h4 className="text-yellow-800 font-bold mb-3 flex items-center">
                    <AlertTriangle size={20} className="mr-2" />
                    Confirmar Carga de Inventario
                  </h4>
                  <div className="text-sm text-yellow-800 space-y-2">
                    <p className="font-semibold">📁 Archivo: {uploadFile.name}</p>
                    <p className="text-xs">Tamaño: {(uploadFile.size / 1024).toFixed(2)} KB</p>
                    <div className="mt-3 p-3 bg-yellow-100 rounded border border-yellow-300">
                      <p className="font-bold text-yellow-900 mb-2">⚠️ IMPORTANTE:</p>
                      <ul className="text-xs space-y-1 list-disc list-inside">
                        <li>Este archivo reemplazará el inventario actual</li>
                        <li>Solo se mostrarán los productos incluidos en este Excel</li>
                        <li>Los productos no incluidos quedarán ocultos del inventario</li>
                        <li>Esta acción actualizará stocks y precios</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {uploadFile && !showConfirmation && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-sm text-blue-800">
                    <strong>Archivo seleccionado:</strong> {uploadFile.name}
                  </p>
                  <p className="text-xs text-blue-600 mt-1">
                    Tamaño: {(uploadFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              )}

              {/* Barra de progreso */}
              {uploading && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-gray-700">
                    <span>Procesando archivo...</span>
                    <span className="font-semibold">{Math.round(uploadProgress)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                    <div
                      className="bg-blue-600 h-full rounded-full transition-all duration-300 ease-out"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {uploadResult && (
                <div className={`border rounded-lg p-4 ${uploadResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                  {uploadResult.success ? (
                    <>
                      <p className="text-green-800 font-semibold mb-2">✅ {uploadResult.message}</p>
                      <div className="text-sm text-green-700">
                        <p>• Insertados: {uploadResult.productos_insertados}</p>
                        <p>• Actualizados: {uploadResult.productos_actualizados}</p>
                        {uploadResult.errores && uploadResult.errores.length > 0 && (
                          <details className="mt-2">
                            <summary className="cursor-pointer text-yellow-700">
                              ⚠️ {uploadResult.errores.length} errores
                            </summary>
                            <ul className="mt-1 ml-4 text-xs">
                              {uploadResult.errores.slice(0, 5).map((error, idx) => (
                                <li key={idx}>• {error}</li>
                              ))}
                            </ul>
                          </details>
                        )}
                      </div>
                    </>
                  ) : (
                    <p className="text-red-800">❌ {uploadResult.error}</p>
                  )}
                </div>
              )}

              <div className="flex gap-3">
                {uploadResult ? (
                  // Mostrar botón OK cuando hay resultado
                  <button
                    onClick={closeUploadModal}
                    className={`flex-1 px-4 py-3 rounded-lg font-bold text-white text-lg ${
                      uploadResult.success
                        ? 'bg-green-600 hover:bg-green-700'
                        : 'bg-blue-600 hover:bg-blue-700'
                    }`}
                  >
                    {uploadResult.success ? '✓ OK' : 'Cerrar'}
                  </button>
                ) : showConfirmation ? (
                  // Mostrar botones de confirmación
                  <>
                    <button
                      onClick={handleUploadExcel}
                      disabled={uploading}
                      className={`flex-1 flex items-center justify-center px-4 py-2 rounded-lg font-semibold ${
                        uploading
                          ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          : 'bg-green-600 text-white hover:bg-green-700'
                      }`}
                    >
                      {uploading ? (
                        <>
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                          Procesando...
                        </>
                      ) : (
                        <>
                          <Upload size={18} className="mr-2" />
                          Confirmar y Cargar
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => {
                        setUploadFile(null);
                        setShowConfirmation(false);
                        if (fileInputRef.current) {
                          fileInputRef.current.value = '';
                        }
                      }}
                      disabled={uploading}
                      className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Cancelar
                    </button>
                  </>
                ) : (
                  // Botón cerrar por defecto
                  <button
                    onClick={closeUploadModal}
                    className="flex-1 px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
                  >
                    Cerrar
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Inventory;
