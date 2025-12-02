import { useState, useEffect, useRef } from 'react';
import { Search, Upload, X, ChevronLeft, ChevronRight, Receipt, FileText, ChevronUp, ChevronDown } from 'lucide-react';
import api from '../../services/api';

const Sales = () => {
  const [ventas, setVentas] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'fecha', direction: 'desc' });

  // Paginación
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [ultimaCarga, setUltimaCarga] = useState(null);
  const itemsPerPage = 50;

  // Modal de carga Excel
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const fileInputRef = useRef(null);

  // Cargar ventas cuando cambian filtros, página u ordenamiento
  useEffect(() => {
    cargarVentas();
    cargarUltimaCarga();
  }, [currentPage, searchTerm, sortConfig]);

  const cargarUltimaCarga = async () => {
    try {
      const response = await api.get('/ventas/ultima-carga/');
      setUltimaCarga(response.data.fecha_ultima_carga);
    } catch (error) {
      console.error('Error cargando última carga:', error);
    }
  };

  // Debounce para búsqueda (500ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchTerm(searchInput);
      setCurrentPage(1);
    }, 500);

    return () => clearTimeout(timer);
  }, [searchInput]);

  const cargarVentas = async () => {
    try {
      setLoading(true);
      setError(null);

      // Mapeo de campos del frontend a campos del backend
      const fieldMapping = {
        'numero': 'numero',
        'fecha': 'fecha',
        'clienteRut': 'cliente__rut',
        'clienteNombre': 'cliente__nombre',
        'total': 'total'
      };

      const params = {
        page: currentPage,
        page_size: itemsPerPage
      };

      if (searchTerm) params.search = searchTerm;

      // Agregar ordenamiento
      const backendField = fieldMapping[sortConfig.key] || sortConfig.key;
      params.ordering = sortConfig.direction === 'desc' ? `-${backendField}` : backendField;

      const response = await api.get('/ventas/', { params });

      setVentas(response.data.results || []);
      setTotalItems(response.data.count || 0);
      setTotalPages(Math.ceil((response.data.count || 0) / itemsPerPage));

    } catch (error) {
      console.error('Error cargando ventas:', error);
      setError(error.response?.data?.message || error.message || 'Error al cargar ventas');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      const validExtensions = ['.xlsx', '.xls', '.XLS', '.XLSX'];
      const fileExtension = file.name.substring(file.name.lastIndexOf('.'));

      if (!validExtensions.includes(fileExtension)) {
        alert('Por favor selecciona un archivo Excel (.xlsx o .xls)');
        return;
      }

      setUploadFile(file);
      setShowConfirmation(true);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) return;

    try {
      setUploading(true);
      setUploadResult(null);
      setUploadProgress(0);

      const formData = new FormData();
      formData.append('archivo', uploadFile);

      const response = await api.post('/ventas/cargar_excel/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutos
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        }
      });

      setUploadProgress(100);
      setUploadResult(response.data);
      setShowConfirmation(false);
      setUploadFile(null);

      // Recargar ventas
      await cargarVentas();

    } catch (error) {
      console.error('Error subiendo archivo:', error);
      setUploadResult({
        error: error.response?.data?.error || error.message || 'Error desconocido al procesar el archivo'
      });
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const cancelUpload = () => {
    setShowConfirmation(false);
    setUploadFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const closeUploadModal = () => {
    setShowUploadModal(false);
    setUploadResult(null);
    setUploadFile(null);
    setShowConfirmation(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatearFecha = (fecha) => {
    if (!fecha) return '';
    const date = new Date(fecha);
    return date.toLocaleDateString('es-CL');
  };

  const formatearNumero = (numero) => {
    return Number(numero).toLocaleString('es-CL');
  };

  const formatearPrecio = (precio) => {
    return `$${Number(precio).toLocaleString('es-CL')}`;
  };

  const formatearRut = (rut) => {
    if (!rut) return '';
    // RUT está guardado sin puntos ni guión: "100415755"
    // Formato de salida: "10.041.575-5"
    const rutStr = rut.toString().replace(/\./g, '').replace(/-/g, '');

    if (rutStr.length < 2) return rut;

    const dv = rutStr.slice(-1);
    const numero = rutStr.slice(0, -1);

    // Agregar puntos cada 3 dígitos desde la derecha
    const numeroFormateado = numero.replace(/\B(?=(\d{3})+(?!\d))/g, '.');

    return `${numeroFormateado}-${dv}`;
  };

  // Aplanar ventas con detalles para mostrar en tabla
  // El ordenamiento ya viene del backend, no es necesario ordenar aquí
  // Cálculos de precios para Chile (IVA 19%):
  // - Precio Unitario: valor CON IVA (viene del Excel)
  // - Neto: precio sin IVA = Precio Unitario / 1.19
  // - Total: Precio Unitario × Cantidad
  const ventasAplanadas = ventas.flatMap(venta =>
    venta.detalles.map(detalle => {
      const precioUnitario = Number(detalle.precio_unitario) || 0;
      const cantidad = Number(detalle.cantidad) || 0;
      const netoUnitario = Math.round(precioUnitario / 1.19); // Precio sin IVA (redondeado)
      const total = precioUnitario * cantidad; // Total con IVA

      return {
        ventaId: venta.id,
        numero: venta.numero,
        fecha: venta.fecha,
        clienteRut: venta.cliente_rut,
        clienteNombre: venta.cliente_nombre,
        codigo: detalle.producto_codigo || detalle.producto,
        producto: detalle.producto_nombre || detalle.producto_descripcion || '',
        cantidad: cantidad,
        precioUnitario: precioUnitario,
        neto: netoUnitario,
        total: total
      };
    })
  );

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
    setCurrentPage(1); // Volver a primera página al cambiar ordenamiento
  };

  const SortIcon = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) {
      return <ChevronUp size={14} className="text-gray-300" />;
    }
    return sortConfig.direction === 'asc'
      ? <ChevronUp size={14} className="text-blue-600" />
      : <ChevronDown size={14} className="text-blue-600" />;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-2 sm:p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-4 md:p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-gray-800 flex items-center gap-2">
                <Receipt className="text-blue-600" />
                Historial de Ventas
              </h1>
              <p className="text-gray-600 mt-1 text-sm md:text-base">Gestión de ventas históricas desde Excel</p>
            </div>
            <button
              onClick={() => setShowUploadModal(true)}
              className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors w-full sm:w-auto"
            >
              <Upload size={20} />
              Cargar Excel
            </button>
          </div>

          {/* Barra de búsqueda */}
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Buscar por N° documento, cliente (nombre/RUT) o producto..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm md:text-base"
              />
            </div>
          </div>

          {/* Estadísticas */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
            <div className="bg-blue-50 rounded-lg p-3 md:p-4">
              <p className="text-xs md:text-sm text-blue-600 font-medium">Total Ventas</p>
              <p className="text-xl md:text-2xl font-bold text-blue-900">{totalItems}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-3 md:p-4">
              <p className="text-xs md:text-sm text-green-600 font-medium">Última Carga</p>
              <p className="text-base md:text-lg font-bold text-green-900">
                {ultimaCarga ? new Date(ultimaCarga).toLocaleString('es-CL', {
                  year: 'numeric',
                  month: '2-digit',
                  day: '2-digit',
                  hour: '2-digit',
                  minute: '2-digit'
                }) : 'Sin datos'}
              </p>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            <p className="font-medium">Error al cargar ventas</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Tabla de Ventas */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200" style={{ minWidth: '1100px' }}>
              <thead className="bg-gray-50">
                <tr>
                  <th onClick={() => handleSort('numero')} className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none whitespace-nowrap">
                    <div className="flex items-center gap-1">Doc <SortIcon columnKey="numero" /></div>
                  </th>
                  <th onClick={() => handleSort('fecha')} className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none whitespace-nowrap">
                    <div className="flex items-center gap-1">Fecha <SortIcon columnKey="fecha" /></div>
                  </th>
                  <th onClick={() => handleSort('clienteRut')} className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none whitespace-nowrap">
                    <div className="flex items-center gap-1">RUT <SortIcon columnKey="clienteRut" /></div>
                  </th>
                  <th onClick={() => handleSort('clienteNombre')} className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none whitespace-nowrap">
                    <div className="flex items-center gap-1">Cliente <SortIcon columnKey="clienteNombre" /></div>
                  </th>
                  <th onClick={() => handleSort('codigo')} className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none whitespace-nowrap">
                    <div className="flex items-center gap-1">Cod <SortIcon columnKey="codigo" /></div>
                  </th>
                  <th onClick={() => handleSort('producto')} className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none whitespace-nowrap">
                    <div className="flex items-center gap-1">Producto <SortIcon columnKey="producto" /></div>
                  </th>
                  <th onClick={() => handleSort('cantidad')} className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none whitespace-nowrap">
                    <div className="flex items-center justify-center gap-1">Cant <SortIcon columnKey="cantidad" /></div>
                  </th>
                  <th onClick={() => handleSort('precioUnitario')} className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none whitespace-nowrap">
                    <div className="flex items-center justify-end gap-1">P.Unit <SortIcon columnKey="precioUnitario" /></div>
                  </th>
                  <th onClick={() => handleSort('neto')} className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none whitespace-nowrap">
                    <div className="flex items-center justify-end gap-1">Neto <SortIcon columnKey="neto" /></div>
                  </th>
                  <th onClick={() => handleSort('total')} className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none whitespace-nowrap">
                    <div className="flex items-center justify-end gap-1">Total <SortIcon columnKey="total" /></div>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan="10" className="px-4 py-8 text-center text-gray-500">
                      <div className="flex items-center justify-center gap-2">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                        Cargando ventas...
                      </div>
                    </td>
                  </tr>
                ) : ventasAplanadas.length === 0 ? (
                  <tr>
                    <td colSpan="10" className="px-4 py-8 text-center text-gray-500">
                      <FileText className="mx-auto mb-2 text-gray-400" size={48} />
                      <p>No hay ventas registradas</p>
                      <p className="text-sm mt-1">Carga un archivo Excel para comenzar</p>
                    </td>
                  </tr>
                ) : (
                  ventasAplanadas.map((item, index) => (
                    <tr key={`${item.ventaId}-${index}`} className="hover:bg-gray-50 transition-colors">
                      <td className="px-3 py-3 text-sm text-gray-900 whitespace-nowrap">{item.numero || 'S/N'}</td>
                      <td className="px-3 py-3 text-sm text-gray-600 whitespace-nowrap">{formatearFecha(item.fecha)}</td>
                      <td className="px-3 py-3 text-sm text-gray-900 font-mono whitespace-nowrap">{formatearRut(item.clienteRut)}</td>
                      <td className="px-3 py-3 text-sm text-gray-900 whitespace-nowrap max-w-[200px] truncate" title={item.clienteNombre}>{item.clienteNombre}</td>
                      <td className="px-3 py-3 text-sm text-gray-600 font-mono whitespace-nowrap">{item.codigo}</td>
                      <td className="px-3 py-3 text-sm text-gray-900 whitespace-nowrap max-w-[250px] truncate" title={item.producto}>{item.producto}</td>
                      <td className="px-3 py-3 text-sm text-center text-gray-900 whitespace-nowrap">{formatearNumero(item.cantidad)}</td>
                      <td className="px-3 py-3 text-sm text-right text-gray-900 whitespace-nowrap">{formatearPrecio(item.precioUnitario)}</td>
                      <td className="px-3 py-3 text-sm text-right text-gray-900 whitespace-nowrap">{formatearPrecio(item.neto)}</td>
                      <td className="px-3 py-3 text-sm text-right font-semibold text-blue-900 whitespace-nowrap">{formatearPrecio(item.total)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Paginación */}
          {!loading && totalPages > 1 && (
            <div className="bg-gray-50 px-4 py-3 border-t border-gray-200 sm:px-6">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Mostrando <span className="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span> a{' '}
                  <span className="font-medium">{Math.min(currentPage * itemsPerPage, totalItems)}</span> de{' '}
                  <span className="font-medium">{totalItems}</span> registros
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 transition-colors flex items-center gap-1"
                  >
                    <ChevronLeft size={16} />
                    Anterior
                  </button>
                  <span className="px-4 py-1 text-sm text-gray-700">
                    Página {currentPage} de {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 transition-colors flex items-center gap-1"
                  >
                    Siguiente
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal de Carga de Excel */}
        {showUploadModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-800">Cargar Ventas desde Excel</h2>
                <button
                  onClick={closeUploadModal}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <X size={24} />
                </button>
              </div>

              {!uploadResult ? (
                <>
                  <div className="mb-4">
                    <p className="text-gray-600 mb-2">
                      Selecciona un archivo Excel (.xlsx o .xls) con el histórico de ventas.
                    </p>
                  </div>

                  <input
                    type="file"
                    ref={fileInputRef}
                    accept=".xlsx,.xls"
                    onChange={handleFileSelect}
                    className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  />

                  {showConfirmation && uploadFile && (
                    <div className="mt-4 p-4 bg-blue-50 rounded border border-blue-200">
                      <p className="text-sm text-blue-800 mb-3">
                        ¿Deseas cargar el archivo <strong>{uploadFile.name}</strong>?
                      </p>
                      <div className="flex gap-2">
                        <button
                          onClick={handleUpload}
                          disabled={uploading}
                          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                        >
                          {uploading ? 'Procesando...' : 'Confirmar Carga'}
                        </button>
                        <button
                          onClick={cancelUpload}
                          disabled={uploading}
                          className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:bg-gray-100 transition-colors"
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Barra de progreso */}
                  {uploading && (
                    <div className="mt-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-blue-700">Procesando archivo...</span>
                        <span className="text-sm font-semibold text-blue-900">{uploadProgress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-600 mt-2 text-center">
                        Por favor, espera mientras se procesa el archivo...
                      </p>
                    </div>
                  )}
                </>
              ) : (
                <div>
                  {uploadResult.error ? (
                    <div className="bg-red-50 border border-red-200 rounded p-4">
                      <div className="flex items-center mb-3">
                        <div className="flex-shrink-0">
                          <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div className="ml-3">
                          <h3 className="text-sm font-medium text-red-800">Error al procesar el archivo</h3>
                        </div>
                      </div>
                      <p className="text-red-700 text-sm">{uploadResult.error}</p>
                    </div>
                  ) : (
                    <div className="bg-green-50 border border-green-200 rounded p-4">
                      <div className="flex items-center mb-3">
                        <div className="flex-shrink-0">
                          <svg className="h-6 w-6 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div className="ml-3">
                          <h3 className="text-sm font-medium text-green-800">¡Archivo procesado exitosamente!</h3>
                        </div>
                      </div>
                      <p className="text-green-700 text-sm mb-3">{uploadResult.message}</p>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-700">Ventas insertadas:</span>
                          <span className="font-semibold text-green-700">{uploadResult.ventas_insertadas}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-700">Detalles insertados:</span>
                          <span className="font-semibold text-green-700">{uploadResult.detalles_insertados}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-700">Clientes creados:</span>
                          <span className="font-semibold text-blue-700">{uploadResult.clientes_creados}</span>
                        </div>
                        {uploadResult.ventas_duplicadas > 0 && (
                          <div className="flex justify-between">
                            <span className="text-gray-700">Ventas duplicadas (omitidas):</span>
                            <span className="font-semibold text-orange-700">{uploadResult.ventas_duplicadas}</span>
                          </div>
                        )}
                        {uploadResult.productos_no_encontrados > 0 && (
                          <div className="flex justify-between">
                            <span className="text-gray-700">Productos no encontrados:</span>
                            <span className="font-semibold text-yellow-700">{uploadResult.productos_no_encontrados}</span>
                          </div>
                        )}
                      </div>
                      {uploadResult.errores && uploadResult.errores.length > 0 && (
                        <details className="mt-4">
                          <summary className="text-sm text-red-600 cursor-pointer hover:text-red-700">
                            Ver errores ({uploadResult.errores.length})
                          </summary>
                          <ul className="mt-2 text-xs text-red-600 list-disc list-inside max-h-40 overflow-y-auto bg-white p-2 rounded">
                            {uploadResult.errores.map((err, idx) => (
                              <li key={idx}>{err}</li>
                            ))}
                          </ul>
                        </details>
                      )}
                    </div>
                  )}
                  <button
                    onClick={closeUploadModal}
                    className="mt-4 w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors font-medium"
                  >
                    OK
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Sales;
