import { useState, useEffect } from 'react';
import { Search, Mail, Star, User, TrendingUp } from 'lucide-react';
import { clientesService } from '../../services/api';

const Customers = () => {
  const [clientes, setClientes] = useState([]);
  const [filteredClientes, setFilteredClientes] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [tipoCliente, setTipoCliente] = useState('todos'); // todos, frecuentes, normales
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Estados de paginación
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 50;

  // Estados de estadísticas globales
  const [stats, setStats] = useState({
    totalClientes: 0,
    clientesFrecuentes: 0,
    clientesNormales: 0,
    elegiblesOfertas: 0
  });

  useEffect(() => {
    cargarEstadisticas();
    cargarClientes();
  }, [currentPage]);

  useEffect(() => {
    filtrarClientes();
  }, [searchTerm, tipoCliente, clientes]);

  const cargarEstadisticas = async () => {
    try {
      const response = await clientesService.getStats();
      setStats({
        totalClientes: response.data.total_clientes || 0,
        clientesFrecuentes: response.data.clientes_frecuentes || 0,
        clientesNormales: response.data.clientes_normales || 0,
        elegiblesOfertas: response.data.elegibles_ofertas || 0
      });
    } catch (error) {
      console.error('Error cargando estadísticas:', error);
    }
  };

  const cargarClientes = async () => {
    try {
      setLoading(true);
      setError(null);

      // Consumir API paginada del backend
      const response = await clientesService.getAll({
        page: currentPage,
        page_size: pageSize
      });

      // Django REST Framework retorna: { count, next, previous, results }
      const paginatedData = response.data;

      // Verificar si tiene estructura paginada o es un array directo
      let clientesData = [];
      let totalCount = 0;

      if (paginatedData.results && Array.isArray(paginatedData.results)) {
        // Respuesta paginada
        clientesData = paginatedData.results;
        totalCount = paginatedData.count || 0;
      } else if (Array.isArray(paginatedData)) {
        // Respuesta directa (array)
        clientesData = paginatedData;
        totalCount = paginatedData.length;
      } else {
        console.error('Formato de respuesta inesperado:', paginatedData);
        throw new Error('Formato de respuesta inválido');
      }

      // Mapear datos del backend al formato esperado por el frontend
      const clientesFormateados = clientesData.map(cliente => ({
        id: cliente.id,
        nombre: cliente.nombre,
        correo: cliente.correo,
        telefono: cliente.telefono || 'N/A',
        totalCompras: cliente.total_compras || 0,
        montoTotal: cliente.monto_total || 0,
        ultimaCompra: cliente.ultima_compra,
        frecuencia: cliente.frecuencia || 'normal'
      }));

      setClientes(clientesFormateados);
      setTotalCount(totalCount);
      setTotalPages(Math.ceil(totalCount / pageSize));

    } catch (error) {
      console.error('Error cargando clientes:', error);
      setError(error.response?.data?.message || error.message || 'Error al cargar clientes');
    } finally {
      setLoading(false);
    }
  };

  const filtrarClientes = () => {
    let resultado = clientes;

    // Filtrar por término de búsqueda
    if (searchTerm) {
      resultado = resultado.filter(
        (c) =>
          c.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.correo.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filtrar por tipo de cliente
    if (tipoCliente === 'frecuentes') {
      resultado = resultado.filter((c) => c.frecuencia === 'frecuente');
    } else if (tipoCliente === 'normales') {
      resultado = resultado.filter((c) => c.frecuencia === 'normal');
    }

    // Ordenar por total de compras descendente
    resultado.sort((a, b) => b.totalCompras - a.totalCompras);

    setFilteredClientes(resultado);
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

  const enviarOfertasMasivas = () => {
    alert(`Se enviarán ofertas a ${stats.elegiblesOfertas} clientes frecuentes con más de 5 compras.`);
    // Aquí se implementará la lógica de envío de correos
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-4 text-xl text-gray-600">Cargando clientes...</span>
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
            <h3 className="text-lg font-semibold text-red-800">Error al cargar clientes</h3>
          </div>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={cargarClientes}
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
        <h1 className="text-3xl font-bold text-gray-800">Gestión de Clientes</h1>
        <button
          onClick={enviarOfertasMasivas}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          <Mail size={20} />
          Enviar Ofertas a Clientes Frecuentes
        </button>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Clientes</p>
              <p className="text-3xl font-bold mt-2">{stats.totalClientes}</p>
            </div>
            <User size={40} className="text-blue-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Clientes Frecuentes</p>
              <p className="text-3xl font-bold mt-2 text-green-600">
                {stats.clientesFrecuentes}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <Star size={24} className="text-green-600" />
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Clientes Normales</p>
              <p className="text-3xl font-bold mt-2 text-gray-600">
                {stats.clientesNormales}
              </p>
            </div>
            <User size={40} className="text-gray-400" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Elegibles para Ofertas</p>
              <p className="text-3xl font-bold mt-2 text-purple-600">
                {stats.elegiblesOfertas}
              </p>
              <p className="text-xs text-gray-500 mt-1">&gt;5 compras</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <Mail size={24} className="text-purple-600" />
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
              placeholder="Buscar por nombre o correo..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2">
            <TrendingUp size={20} className="text-gray-400" />
            <select
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={tipoCliente}
              onChange={(e) => setTipoCliente(e.target.value)}
            >
              <option value="todos">Todos los clientes</option>
              <option value="frecuentes">Clientes frecuentes (≥5 compras)</option>
              <option value="normales">Clientes normales (&lt;5 compras)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tabla de clientes */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tipo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nombre
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Correo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Compras
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Monto Total
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Última Compra
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredClientes.map((cliente) => (
                <tr key={cliente.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    {cliente.frecuencia === 'frecuente' ? (
                      <span className="flex items-center text-green-600">
                        <Star size={16} className="mr-1 fill-current" />
                        <span className="text-xs font-semibold">Frecuente</span>
                      </span>
                    ) : (
                      <span className="text-gray-500 text-xs">Normal</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {cliente.nombre}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {cliente.correo}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                    {cliente.totalCompras}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(cliente.montoTotal)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(cliente.ultimaCompra)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {cliente.frecuencia === 'frecuente' && cliente.totalCompras >= 5 && (
                      <button
                        className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
                        onClick={() => alert(`Enviar oferta a ${cliente.nombre}`)}
                      >
                        <Mail size={16} />
                        Enviar Oferta
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredClientes.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No se encontraron clientes
          </div>
        )}

        {/* Controles de paginación */}
        {totalPages > 1 && (
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Mostrando <span className="font-semibold">{(currentPage - 1) * pageSize + 1}</span> a{' '}
                <span className="font-semibold">
                  {Math.min(currentPage * pageSize, totalCount)}
                </span>{' '}
                de <span className="font-semibold">{totalCount}</span> clientes
              </div>

              <div className="flex items-center gap-2">
                {/* Botón Primera Página */}
                <button
                  onClick={() => setCurrentPage(1)}
                  disabled={currentPage === 1}
                  className={`px-3 py-1 rounded ${
                    currentPage === 1
                      ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  Primera
                </button>

                {/* Botón Anterior */}
                <button
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 1}
                  className={`px-3 py-1 rounded ${
                    currentPage === 1
                      ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  Anterior
                </button>

                {/* Indicador de página actual */}
                <span className="px-4 py-1 text-sm text-gray-700">
                  Página <span className="font-semibold">{currentPage}</span> de{' '}
                  <span className="font-semibold">{totalPages}</span>
                </span>

                {/* Botón Siguiente */}
                <button
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className={`px-3 py-1 rounded ${
                    currentPage === totalPages
                      ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  Siguiente
                </button>

                {/* Botón Última Página */}
                <button
                  onClick={() => setCurrentPage(totalPages)}
                  disabled={currentPage === totalPages}
                  className={`px-3 py-1 rounded ${
                    currentPage === totalPages
                      ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  Última
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Customers;
