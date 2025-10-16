import { useState, useEffect } from 'react';
import { Search, Mail, Star, User, TrendingUp } from 'lucide-react';
import { clientesService } from '../../services/api';

const Customers = () => {
  const [clientes, setClientes] = useState([]);
  const [filteredClientes, setFilteredClientes] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [tipoCliente, setTipoCliente] = useState('todos'); // todos, frecuentes, normales
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarClientes();
  }, []);

  useEffect(() => {
    filtrarClientes();
  }, [searchTerm, tipoCliente, clientes]);

  const cargarClientes = async () => {
    try {
      setLoading(true);
      // Datos simulados - reemplazar con llamada API real
      const datosSimulados = [
        { id: 1, nombre: 'María González', correo: 'maria.gonzalez@email.com', telefono: '+56912345678', totalCompras: 15, montoTotal: 2500000, ultimaCompra: '2025-10-10', frecuencia: 'frecuente' },
        { id: 2, nombre: 'Juan Pérez', correo: 'juan.perez@email.com', telefono: '+56987654321', totalCompras: 8, montoTotal: 1200000, ultimaCompra: '2025-10-12', frecuencia: 'frecuente' },
        { id: 3, nombre: 'Ana Silva', correo: 'ana.silva@email.com', telefono: '+56923456789', totalCompras: 3, montoTotal: 450000, ultimaCompra: '2025-10-05', frecuencia: 'normal' },
        { id: 4, nombre: 'Pedro Martínez', correo: 'pedro.martinez@email.com', telefono: '+56934567890', totalCompras: 12, montoTotal: 1850000, ultimaCompra: '2025-10-13', frecuencia: 'frecuente' },
        { id: 5, nombre: 'Carmen López', correo: 'carmen.lopez@email.com', telefono: '+56945678901', totalCompras: 7, montoTotal: 980000, ultimaCompra: '2025-10-11', frecuencia: 'frecuente' },
        { id: 6, nombre: 'Roberto Díaz', correo: 'roberto.diaz@email.com', telefono: '+56956789012', totalCompras: 2, montoTotal: 280000, ultimaCompra: '2025-09-28', frecuencia: 'normal' },
        { id: 7, nombre: 'Laura Fernández', correo: 'laura.fernandez@email.com', telefono: '+56967890123', totalCompras: 18, montoTotal: 3200000, ultimaCompra: '2025-10-14', frecuencia: 'frecuente' },
        { id: 8, nombre: 'Carlos Rojas', correo: 'carlos.rojas@email.com', telefono: '+56978901234', totalCompras: 4, montoTotal: 620000, ultimaCompra: '2025-10-08', frecuencia: 'normal' },
        { id: 9, nombre: 'Patricia Muñoz', correo: 'patricia.munoz@email.com', telefono: '+56989012345', totalCompras: 10, montoTotal: 1450000, ultimaCompra: '2025-10-13', frecuencia: 'frecuente' },
        { id: 10, nombre: 'Jorge Soto', correo: 'jorge.soto@email.com', telefono: '+56990123456', totalCompras: 6, montoTotal: 850000, ultimaCompra: '2025-10-09', frecuencia: 'frecuente' },
        { id: 11, nombre: 'Sofía Castro', correo: 'sofia.castro@email.com', telefono: '+56901234567', totalCompras: 1, montoTotal: 120000, ultimaCompra: '2025-09-15', frecuencia: 'normal' },
        { id: 12, nombre: 'Diego Ramírez', correo: 'diego.ramirez@email.com', telefono: '+56912345670', totalCompras: 14, montoTotal: 2100000, ultimaCompra: '2025-10-12', frecuencia: 'frecuente' },
      ];
      setClientes(datosSimulados);
      setLoading(false);
    } catch (error) {
      console.error('Error cargando clientes:', error);
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
        <div className="text-xl">Cargando clientes...</div>
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
