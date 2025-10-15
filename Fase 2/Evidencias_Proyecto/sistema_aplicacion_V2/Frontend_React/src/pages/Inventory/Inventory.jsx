import { useState, useEffect } from 'react';
import { Search, AlertTriangle, Package, Filter } from 'lucide-react';
import { productosService } from '../../services/api';

const Inventory = () => {
  const [productos, setProductos] = useState([]);
  const [filteredProductos, setFilteredProductos] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filtroStock, setFiltroStock] = useState('todos'); // todos, bajo, normal
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarProductos();
  }, []);

  useEffect(() => {
    filtrarProductos();
  }, [searchTerm, filtroStock, productos]);

  const cargarProductos = async () => {
    try {
      setLoading(true);
      // Datos simulados - reemplazar con llamada API real
      const datosSimulados = [
        { id: 1, codigo: 'MED-001', descripcion: 'Paracetamol 500mg', stock: 850, stockMinimo: 200, categoria: 'Analgésico' },
        { id: 2, codigo: 'MED-002', descripcion: 'Ibuprofeno 400mg', stock: 720, stockMinimo: 150, categoria: 'Antiinflamatorio' },
        { id: 3, codigo: 'MED-003', descripcion: 'Amoxicilina 500mg', stock: 45, stockMinimo: 100, categoria: 'Antibiótico' },
        { id: 4, codigo: 'MED-004', descripcion: 'Loratadina 10mg', stock: 580, stockMinimo: 100, categoria: 'Antihistamínico' },
        { id: 5, codigo: 'MED-005', descripcion: 'Omeprazol 20mg', stock: 520, stockMinimo: 150, categoria: 'Gastroprotector' },
        { id: 6, codigo: 'MED-006', descripcion: 'Atorvastatina 20mg', stock: 35, stockMinimo: 80, categoria: 'Hipolipemiante' },
        { id: 7, codigo: 'MED-007', descripcion: 'Metformina 850mg', stock: 450, stockMinimo: 120, categoria: 'Antidiabético' },
        { id: 8, codigo: 'MED-008', descripcion: 'Losartán 50mg', stock: 420, stockMinimo: 100, categoria: 'Antihipertensivo' },
        { id: 9, codigo: 'MED-009', descripcion: 'Clonazepam 0.5mg', stock: 25, stockMinimo: 50, categoria: 'Ansiolítico' },
        { id: 10, codigo: 'MED-010', descripcion: 'Enalapril 10mg', stock: 350, stockMinimo: 80, categoria: 'Antihipertensivo' },
        { id: 11, codigo: 'MED-011', descripcion: 'Levotiroxina 100mcg', stock: 280, stockMinimo: 100, categoria: 'Hormona tiroidea' },
        { id: 12, codigo: 'MED-012', descripcion: 'Salbutamol Inhalador', stock: 15, stockMinimo: 40, categoria: 'Broncodilatador' },
        { id: 13, codigo: 'MED-013', descripcion: 'Diclofenaco 50mg', stock: 380, stockMinimo: 100, categoria: 'Antiinflamatorio' },
        { id: 14, codigo: 'MED-014', descripcion: 'Ranitidina 150mg', stock: 420, stockMinimo: 120, categoria: 'Gastroprotector' },
        { id: 15, codigo: 'MED-015', descripcion: 'Aspirina 100mg', stock: 650, stockMinimo: 150, categoria: 'Antiagregante' },
      ];
      setProductos(datosSimulados);
      setLoading(false);
    } catch (error) {
      console.error('Error cargando productos:', error);
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
        <div className="text-xl">Cargando inventario...</div>
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
