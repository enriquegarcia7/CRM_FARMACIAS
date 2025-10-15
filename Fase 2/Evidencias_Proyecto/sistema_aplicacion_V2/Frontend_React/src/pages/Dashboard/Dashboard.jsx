import { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { DollarSign, TrendingUp, Package, Users } from 'lucide-react';
import { dashboardService, transaccionesService } from '../../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalVentas: 0,
    ventasMes: 0,
    productosStock: 0,
    clientesActivos: 0,
  });

  const [topProductos, setTopProductos] = useState([]);
  const [ventasMensuales, setVentasMensuales] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarDatos();
    // Actualizar cada 30 segundos
    const interval = setInterval(cargarDatos, 30000);
    return () => clearInterval(interval);
  }, []);

  const cargarDatos = async () => {
    try {
      setLoading(true);

      // Datos simulados - reemplazar con llamadas API reales
      setStats({
        totalVentas: 45780000,
        ventasMes: 8950000,
        productosStock: 342,
        clientesActivos: 128,
      });

      // Top 10 productos más vendidos
      setTopProductos([
        { nombre: 'Paracetamol 500mg', cantidad: 850, ventas: 2550000 },
        { nombre: 'Ibuprofeno 400mg', cantidad: 720, ventas: 2160000 },
        { nombre: 'Amoxicilina 500mg', cantidad: 650, ventas: 3250000 },
        { nombre: 'Loratadina 10mg', cantidad: 580, ventas: 1740000 },
        { nombre: 'Omeprazol 20mg', cantidad: 520, ventas: 2080000 },
        { nombre: 'Atorvastatina 20mg', cantidad: 480, ventas: 2880000 },
        { nombre: 'Metformina 850mg', cantidad: 450, ventas: 1800000 },
        { nombre: 'Losartán 50mg', cantidad: 420, ventas: 2100000 },
        { nombre: 'Clonazepam 0.5mg', cantidad: 380, ventas: 1900000 },
        { nombre: 'Enalapril 10mg', cantidad: 350, ventas: 1400000 },
      ]);

      // Ventas mensuales del año
      setVentasMensuales([
        { mes: 'Ene', ventas: 6500000 },
        { mes: 'Feb', ventas: 7200000 },
        { mes: 'Mar', ventas: 6800000 },
        { mes: 'Abr', ventas: 7500000 },
        { mes: 'May', ventas: 8100000 },
        { mes: 'Jun', ventas: 7800000 },
        { mes: 'Jul', ventas: 8500000 },
        { mes: 'Ago', ventas: 8200000 },
        { mes: 'Sep', ventas: 8800000 },
        { mes: 'Oct', ventas: 8950000 },
      ]);

      setLoading(false);
    } catch (error) {
      console.error('Error cargando datos del dashboard:', error);
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
    }).format(value);
  };

  const StatCard = ({ icon: Icon, title, value, trend, color }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-500 text-sm">{title}</p>
          <p className="text-2xl font-bold mt-2">{value}</p>
          {trend && (
            <div className="flex items-center mt-2 text-green-600 text-sm">
              <TrendingUp size={16} />
              <span className="ml-1">{trend}</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon size={24} className="text-white" />
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-xl">Cargando dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>

      {/* Tarjetas de estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={DollarSign}
          title="Total Ventas"
          value={formatCurrency(stats.totalVentas)}
          trend="+12.5%"
          color="bg-green-500"
        />
        <StatCard
          icon={TrendingUp}
          title="Ventas del Mes"
          value={formatCurrency(stats.ventasMes)}
          trend="+8.2%"
          color="bg-blue-500"
        />
        <StatCard
          icon={Package}
          title="Productos en Stock"
          value={stats.productosStock}
          color="bg-purple-500"
        />
        <StatCard
          icon={Users}
          title="Clientes Activos"
          value={stats.clientesActivos}
          trend="+5.3%"
          color="bg-orange-500"
        />
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico de ventas mensuales */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Ventas Mensuales 2025</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={ventasMensuales}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="mes" />
              <YAxis />
              <Tooltip
                formatter={(value) => formatCurrency(value)}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="ventas"
                stroke="#3b82f6"
                strokeWidth={2}
                name="Ventas"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Top 10 productos más vendidos */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Top 10 Productos Más Vendidos</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topProductos.slice(0, 5)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="nombre" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip
                formatter={(value, name) => [
                  name === 'cantidad' ? value : formatCurrency(value),
                  name === 'cantidad' ? 'Unidades' : 'Ventas',
                ]}
              />
              <Legend />
              <Bar dataKey="cantidad" fill="#8b5cf6" name="Cantidad Vendida" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Tabla de top productos */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">Detalle Top 10 Productos</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    #
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Producto
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Unidades Vendidas
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Ventas
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {topProductos.map((producto, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {index + 1}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {producto.nombre}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {producto.cantidad}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(producto.ventas)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
