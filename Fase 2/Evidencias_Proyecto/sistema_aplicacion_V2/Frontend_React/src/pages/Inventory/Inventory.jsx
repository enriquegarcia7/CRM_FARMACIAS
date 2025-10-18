import { useState, useEffect } from 'react';
import { Search, AlertTriangle, Package, Filter } from 'lucide-react';
import { productosService } from '../../services/api';

const Inventory = () => {
  const [productos, setProductos] = useState([]);
  const [filteredProductos, setFilteredProductos] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filtroStock, setFiltroStock] = useState('todos'); // todos, bajo, normal
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    cargarProductos();
  }, []);

  useEffect(() => {
    filtrarProductos();
  }, [searchTerm, filtroStock, productos]);

  const cargarProductos = async () => {
    try {
      setLoading(true);
      setError(null);

      // Consumir API real del backend
      const response = await productosService.getAll();

      // Mapear datos del backend al formato esperado por el frontend
      const productosFormateados = response.data.map(producto => ({
        id: producto.id,
        codigo: producto.codigo,
        descripcion: producto.descripcion || producto.nombre,
        stock: producto.stock_actual,
        stockMinimo: producto.stock_minimo,
        categoria: producto.categoria
      }));

      setProductos(productosFormateados);
    } catch (error) {
      console.error('Error cargando productos:', error);
      setError(error.response?.data?.message || error.message || 'Error al cargar inventario');
    } finally {
      setLoading(false);
    }
  };

  const filtrarProductos = () => {
    let resultado = productos;

    // Filtrar por término de búsqueda
    if (searchTerm) {
      resultado = resultado.filter(
        (p) =>
          p.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
          p.descripcion.toLowerCase().includes(searchTerm.toLowerCase()) ||
          p.categoria.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filtrar por nivel de stock
    if (filtroStock === 'bajo') {
      resultado = resultado.filter((p) => p.stock < p.stockMinimo);
    } else if (filtroStock === 'normal') {
      resultado = resultado.filter((p) => p.stock >= p.stockMinimo);
    }

    setFilteredProductos(resultado);
  };

  const getStockStatus = (producto) => {
    const porcentaje = (producto.stock / producto.stockMinimo) * 100;
    if (porcentaje < 50) return { color: 'text-red-600 bg-red-100', label: 'Crítico' };
    if (porcentaje < 100) return { color: 'text-yellow-600 bg-yellow-100', label: 'Bajo' };
    return { color: 'text-green-600 bg-green-100', label: 'Normal' };
  };

  const productosBajoStock = productos.filter((p) => p.stock < p.stockMinimo).length;

  if (loading) {
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
        {productosBajoStock > 0 && (
          <div className="flex items-center bg-red-100 text-red-700 px-4 py-2 rounded-lg">
            <AlertTriangle size={20} className="mr-2" />
            <span className="font-semibold">
              {productosBajoStock} productos con bajo stock
            </span>
          </div>
        )}
      </div>

      {/* Estadísticas rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Productos</p>
              <p className="text-3xl font-bold mt-2">{productos.length}</p>
            </div>
            <Package size={40} className="text-blue-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Stock Normal</p>
              <p className="text-3xl font-bold mt-2 text-green-600">
                {productos.filter((p) => p.stock >= p.stockMinimo).length}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <Package size={24} className="text-green-600" />
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Bajo Stock</p>
              <p className="text-3xl font-bold mt-2 text-red-600">
                {productosBajoStock}
              </p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              <AlertTriangle size={24} className="text-red-600" />
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
              placeholder="Buscar por código, descripción o categoría..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={20} className="text-gray-400" />
            <select
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={filtroStock}
              onChange={(e) => setFiltroStock(e.target.value)}
            >
              <option value="todos">Todos los productos</option>
              <option value="bajo">Bajo stock</option>
              <option value="normal">Stock normal</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tabla de productos */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Código
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Descripción
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Categoría
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Stock Actual
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Stock Mínimo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredProductos.map((producto) => {
                const status = getStockStatus(producto);
                return (
                  <tr key={producto.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {producto.codigo}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {producto.descripcion}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {producto.categoria}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                      {producto.stock}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {producto.stockMinimo}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${status.color}`}
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
        {filteredProductos.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No se encontraron productos
          </div>
        )}
      </div>
    </div>
  );
};

export default Inventory;
