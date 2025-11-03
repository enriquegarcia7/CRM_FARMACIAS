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

  useEffect(() => {
    cargarClientes();
  }, []);

  useEffect(() => {
    filtrarClientes();
  }, [searchTerm, tipoCliente, clientes]);

  const cargarClientes = async () => {
    try {
      setLoading(true);
      setError(null);

      // Consumir API real del backend
      const response = await clientesService.getAll();

      // Mapear datos del backend al formato esperado por el frontend
      const clientesFormateados = response.data.map(cliente => ({
        id: cliente.id,
        nombre: cliente.nombre,
        correo: cliente.correo,
        telefono: cliente.telefono || 'N/A',
        totalCompras: cliente.transacciones?.length || 0,
        montoTotal: cliente.monto_total_gastado || 0,
        ultimaCompra: cliente.fecha_registro,
        frecuencia: (cliente.transacciones?.length || 0) >= 5 ? 'frecuente' : 'normal'
      }));

      setClientes(clientesFormateados);
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
          c.correo.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.telefono.includes(searchTerm)
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
    const clientesFrecuentes = clientes.filter(c => c.frecuencia === 'frecuente' && c.totalCompras >= 5);
    alert(`Se enviarán ofertas a ${clientesFrecuentes.length} clientes frecuentes con más de 5 compras.`);
    // Aquí se implementará la lógica de envío de correos
  };

  const clientesFrecuentes = clientes.filter((c) => c.frecuencia === 'frecuente').length;
  const clientesNormales = clientes.filter((c) => c.frecuencia === 'normal').length;
  const clientesElegiblesOfertas = clientes.filter((c) => c.frecuencia === 'frecuente' && c.totalCompras >= 5).length;

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
              <p className="text-3xl font-bold mt-2">{clientes.length}</p>
            </div>
            <User size={40} className="text-blue-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Clientes Frecuentes</p>
              <p className="text-3xl font-bold mt-2 text-green-600">
                {clientesFrecuentes}
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
                {clientesNormales}
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
                {clientesElegiblesOfertas}
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
              placeholder="Buscar por nombre, correo o teléfono..."
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
                  Teléfono
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
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {cliente.telefono}
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
      </div>
    </div>
  );
};

export default Customers;
