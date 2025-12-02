import { useState, useEffect } from 'react';
import { Search, DollarSign, TrendingUp, Package, Calendar, Filter, ChevronUp, ChevronDown } from 'lucide-react';
import { ventasService } from '../../services/api';

// Ventas component with sortable columns - v2
const Ventas = () => {
  const [ventas, setVentas] = useState([]);
  const [filteredVentas, setFilteredVentas] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'fecha', direction: 'desc' });
  const [stats, setStats] = useState({
    totalVentas: 0,
    totalMonto: 0,
    promedioVenta: 0,
    productosVendidos: 0
  });

  useEffect(() => {
    cargarVentas();
  }, []);

  useEffect(() => {
    filtrarVentas();
  }, [searchTerm, ventas, sortConfig]);

  const cargarVentas = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await ventasService.getAll();

      // Mapear datos del backend al formato esperado por el frontend
      // Cada venta tiene detalles con productos, extraemos info del primer detalle
      const ventasFormateadas = response.data.map(venta => {
        const primerDetalle = venta.detalles?.[0];
        return {
          id: venta.id,
          numero: venta.numero || '',
          fecha: venta.fecha,
          cliente: venta.cliente_nombre || 'Cliente Anónimo',
          clienteRut: venta.cliente_rut || '',
          clienteId: venta.cliente,
          producto: primerDetalle?.producto_descripcion || primerDetalle?.producto_nombre || 'N/A',
          productoId: primerDetalle?.producto,
          cantidad: primerDetalle?.cantidad || 0,
          precio_unitario: primerDetalle?.precio_unitario || 0,
          neto: primerDetalle?.neto || 0,
          total: venta.total || 0,
          metodo_pago: venta.metodo_pago || 'Efectivo'
        };
      });

      setVentas(ventasFormateadas);
      calcularEstadisticas(ventasFormateadas);
    } catch (error) {
      console.error('Error cargando ventas:', error);
      setError(error.response?.data?.message || error.message || 'Error al cargar ventas');
    } finally {
      setLoading(false);
    }
  };

  const calcularEstadisticas = (ventasData) => {
    const totalVentas = ventasData.length;
    const totalMonto = ventasData.reduce((sum, venta) => sum + venta.total, 0);
    const promedioVenta = totalVentas > 0 ? totalMonto / totalVentas : 0;
    const productosVendidos = ventasData.reduce((sum, venta) => sum + venta.cantidad, 0);

    setStats({
      totalVentas,
      totalMonto,
      promedioVenta,
      productosVendidos
    });
  };

  const filtrarVentas = () => {
    let resultado = ventas;

    // Filtrar por término de búsqueda
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      resultado = resultado.filter(
        (v) =>
          (v.numero && v.numero.toLowerCase().includes(term)) ||
          (v.cliente && v.cliente.toLowerCase().includes(term)) ||
          (v.clienteRut && v.clienteRut.toLowerCase().replace(/\./g, '').replace(/-/g, '').includes(term.replace(/\./g, '').replace(/-/g, ''))) ||
          (v.producto && v.producto.toLowerCase().includes(term))
      );
    }

    // Ordenar según configuración
    resultado = [...resultado].sort((a, b) => {
      let aValue = a[sortConfig.key];
      let bValue = b[sortConfig.key];

      // Manejar fechas
      if (sortConfig.key === 'fecha') {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      }

      // Manejar strings
      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });

    setFilteredVentas(resultado);
  };

  const handleSort = (key) => {
    setSortConfig(prev => {
      const newDirection = prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc';
      return { key, direction: newDirection };
    });
  };

  const renderSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey) {
      return <ChevronUp size={14} className="text-gray-300" />;
    }
    return sortConfig.direction === 'asc'
      ? <ChevronUp size={14} className="text-blue-600" />
      : <ChevronDown size={14} className="text-blue-600" />;
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
    }).format(value);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-CL', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-4 text-xl text-gray-600">Cargando ventas...</span>
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
            <h3 className="text-lg font-semibold text-red-800">Error al cargar ventas</h3>
          </div>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={cargarVentas}
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
        <h1 className="text-3xl font-bold text-gray-800">Gestión de Ventas</h1>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Ventas</p>
              <p className="text-3xl font-bold mt-2">{stats.totalVentas}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <TrendingUp size={24} className="text-blue-600" />
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Monto Total</p>
              <p className="text-2xl font-bold mt-2 text-green-600">
                {formatCurrency(stats.totalMonto)}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <DollarSign size={24} className="text-green-600" />
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Promedio por Venta</p>
              <p className="text-2xl font-bold mt-2 text-purple-600">
                {formatCurrency(stats.promedioVenta)}
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <DollarSign size={24} className="text-purple-600" />
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Productos Vendidos</p>
              <p className="text-3xl font-bold mt-2 text-orange-600">
                {stats.productosVendidos}
              </p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
              <Package size={24} className="text-orange-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Búsqueda */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Buscar por N° documento, cliente (nombre/RUT) o producto..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Tabla de ventas */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                  onClick={() => handleSort('id')}
                >
                  <div className="flex items-center gap-1">
                    ID {renderSortIcon('id')}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                  onClick={() => handleSort('fecha')}
                >
                  <div className="flex items-center gap-1">
                    Fecha {renderSortIcon('fecha')}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                  onClick={() => handleSort('cliente')}
                >
                  <div className="flex items-center gap-1">
                    Cliente {renderSortIcon('cliente')}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                  onClick={() => handleSort('producto')}
                >
                  <div className="flex items-center gap-1">
                    Producto {renderSortIcon('producto')}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                  onClick={() => handleSort('cantidad')}
                >
                  <div className="flex items-center gap-1">
                    Cantidad {renderSortIcon('cantidad')}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                  onClick={() => handleSort('precio_unitario')}
                >
                  <div className="flex items-center gap-1">
                    Precio Unit. {renderSortIcon('precio_unitario')}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                  onClick={() => handleSort('neto')}
                >
                  <div className="flex items-center gap-1">
                    Neto {renderSortIcon('neto')}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                  onClick={() => handleSort('total')}
                >
                  <div className="flex items-center gap-1">
                    Total {renderSortIcon('total')}
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Método Pago
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredVentas.map((venta) => (
                <tr key={venta.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    #{venta.id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(venta.fecha)}
                  </td>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">
                    {venta.cliente}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {venta.producto}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center">
                    {venta.cantidad}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(venta.precio_unitario)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatCurrency(venta.neto)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">
                    {formatCurrency(venta.total)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                      venta.metodo_pago === 'Efectivo'
                        ? 'bg-green-100 text-green-800'
                        : venta.metodo_pago === 'Tarjeta'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-purple-100 text-purple-800'
                    }`}>
                      {venta.metodo_pago}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredVentas.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No se encontraron ventas
          </div>
        )}
      </div>
    </div>
  );
};

export default Ventas;
