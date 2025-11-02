import { useState, useEffect } from 'react';
import { Search, Filter, Tag, TrendingDown, Calendar, Package, ChevronLeft, ChevronRight, Building2 } from 'lucide-react';
import { ofertasService } from '../../services/api';

const OfertasLaboratorio = () => {
  const [ofertas, setOfertas] = useState([]);
  const [laboratorios, setLaboratorios] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchInput, setSearchInput] = useState(''); // Para debounce
  const [selectedLab, setSelectedLab] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Paginación backend
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 50;

  // Cargar laboratorios solo una vez
  useEffect(() => {
    cargarLaboratorios();
  }, []);

  // Cargar ofertas cuando cambian filtros o página
  useEffect(() => {
    cargarOfertas();
  }, [currentPage, selectedLab, searchTerm]);

  // Debounce para búsqueda (esperar 500ms después de que el usuario termine de escribir)
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchTerm(searchInput);
      setCurrentPage(1); // Reset a página 1 cuando busca
    }, 500);

    return () => clearTimeout(timer);
  }, [searchInput]);

  const cargarLaboratorios = async () => {
    try {
      const response = await ofertasService.getLaboratorios();
      setLaboratorios(response.data.laboratorios || []);
    } catch (error) {
      console.error('Error cargando laboratorios:', error);
    }
  };

  const cargarOfertas = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: currentPage,
        page_size: itemsPerPage,
        activas: true
      };

      if (selectedLab) params.laboratorio = selectedLab;
      if (searchTerm) params.search = searchTerm;

      const response = await ofertasService.getPorLaboratorio(params);

      // Response de DRF PageNumberPagination
      setOfertas(response.data.results || []);
      setTotalItems(response.data.count || 0);
      setTotalPages(Math.ceil((response.data.count || 0) / itemsPerPage));

    } catch (error) {
      console.error('Error cargando ofertas:', error);
      setError(error.response?.data?.message || error.message || 'Error al cargar ofertas');
    } finally {
      setLoading(false);
    }
  };

  // Calcular estadísticas por proveedor (cargar de ofertas actuales en vista)
  const getProveedorStats = () => {
    const stats = {};
    ofertas.forEach(oferta => {
      const proveedor = oferta.proveedor || 'Sin proveedor';
      if (!stats[proveedor]) {
        stats[proveedor] = 0;
      }
      stats[proveedor]++;
    });
    return Object.entries(stats).sort((a, b) => b[1] - a[1]);
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

  const formatPrecio = (precio) => {
    if (!precio) return '$0';
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(precio);
  };

  const formatFecha = (fecha) => {
    if (!fecha) return '-';
    return new Date(fecha).toLocaleDateString('es-CL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const getDescuentoColor = (descuento) => {
    const desc = parseFloat(descuento) || 0;
    if (desc >= 30) return 'text-green-700 bg-green-100';
    if (desc >= 15) return 'text-blue-700 bg-blue-100';
    if (desc > 0) return 'text-yellow-700 bg-yellow-100';
    return 'text-gray-700 bg-gray-100';
  };

  const getDiasVigenciaColor = (dias) => {
    if (dias <= 3) return 'text-red-700 bg-red-100';
    if (dias <= 7) return 'text-yellow-700 bg-yellow-100';
    return 'text-green-700 bg-green-100';
  };

  if (loading && ofertas.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-4 text-xl text-gray-600">Cargando ofertas...</span>
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
            <h3 className="text-lg font-semibold text-red-800">Error al cargar ofertas</h3>
          </div>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={cargarOfertas}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  const proveedorStats = getProveedorStats();
  const indexOfFirstItem = (currentPage - 1) * itemsPerPage + 1;
  const indexOfLastItem = Math.min(currentPage * itemsPerPage, totalItems);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Ofertas</h1>
        <div className="flex items-center bg-blue-100 text-blue-700 px-4 py-2 rounded-lg">
          <Package size={20} className="mr-2" />
          <span className="font-semibold">
            {totalItems.toLocaleString('es-CL')} ofertas vigentes
          </span>
        </div>
      </div>

      {/* Estadísticas por proveedor */}
      {proveedorStats.length > 0 && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start gap-3 mb-3">
            <Building2 size={24} className="text-blue-600 mt-1" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">Proveedores en esta página</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {proveedorStats.map(([proveedor, count]) => (
                  <div key={proveedor} className="bg-white rounded-lg p-3 shadow-sm">
                    <p className="text-sm font-semibold text-gray-700 truncate" title={proveedor}>{proveedor}</p>
                    <p className="text-xl font-bold text-blue-600">{count}</p>
                    <p className="text-xs text-gray-500">en página actual</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Estadísticas rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Ofertas</p>
              <p className="text-3xl font-bold mt-2">{totalItems.toLocaleString('es-CL')}</p>
            </div>
            <TrendingDown size={40} className="text-blue-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Laboratorios</p>
              <p className="text-3xl font-bold mt-2 text-green-600">
                {laboratorios.length}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <Tag size={24} className="text-green-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Filtros y búsqueda */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Buscar por código, descripción, laboratorio o proveedor..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={20} className="text-gray-400" />
            <select
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={selectedLab}
              onChange={(e) => {
                setSelectedLab(e.target.value);
                setCurrentPage(1);
              }}
            >
              <option value="">Todos los laboratorios</option>
              {laboratorios.map((lab) => (
                <option key={lab.laboratorio} value={lab.laboratorio}>
                  {lab.laboratorio} ({lab.total_ofertas})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Tabla de ofertas */}
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
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                  Proveedor
                </th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-28">
                  Código
                </th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-48">
                  Descripción
                </th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                  Laboratorio
                </th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-28">
                  Precio
                </th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                  % Desc.
                </th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                  Vigencia
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {ofertas.map((oferta) => (
                <tr key={oferta.id} className="hover:bg-gray-50">
                  <td className="px-3 py-3 whitespace-nowrap text-sm font-medium text-purple-600">
                    {oferta.proveedor || '-'}
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                    {oferta.codigo_producto || '-'}
                  </td>
                  <td className="px-3 py-3 text-sm text-gray-900" style={{ maxWidth: '300px' }}>
                    <div className="truncate" title={oferta.descripcion}>
                      {oferta.descripcion || '-'}
                    </div>
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap text-sm font-semibold text-blue-600">
                    {oferta.laboratorio || '-'}
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap text-sm font-semibold text-green-700">
                    {formatPrecio(oferta.precio)}
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getDescuentoColor(oferta.descuento_porcentaje)}`}>
                      {parseFloat(oferta.descuento_porcentaje || 0).toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap">
                    <div className="flex flex-col">
                      <span className="text-xs text-gray-900 flex items-center">
                        <Calendar size={12} className="mr-1 text-gray-400" />
                        {formatFecha(oferta.vencimiento_vigencia)}
                      </span>
                      <span className={`mt-1 px-2 py-0.5 rounded-full text-xs font-semibold ${getDiasVigenciaColor(oferta.dias_vigencia)}`}>
                        {oferta.dias_vigencia} días
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {ofertas.length === 0 && !loading && (
          <div className="text-center py-12 text-gray-500">
            No se encontraron ofertas
          </div>
        )}

        {/* Controles de paginación */}
        {ofertas.length > 0 && (
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
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
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
    </div>
  );
};

export default OfertasLaboratorio;
