import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  Users,
  ShoppingCart,
  TrendingUp,
  Tag,
  Database,
  Menu,
  X,
  LogOut,
  CheckCircle,
  Receipt,
  Percent
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';

const Layout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  // Detectar cambios de tamaño de pantalla
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      // En desktop, abrir sidebar por defecto
      if (!mobile && !sidebarOpen) {
        setSidebarOpen(true);
      }
    };

    // Ejecutar al montar
    handleResize();

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Cerrar sidebar al cambiar de ruta en móvil
  useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  }, [location.pathname, isMobile]);

  const handleLogout = async () => {
    if (window.confirm('¿Estás seguro de que deseas cerrar sesión? Deberás volver a autorizar con Google.')) {
      await logout();
      navigate('/login');
    }
  };

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/inventario', icon: Package, label: 'Inventario' },
    { path: '/clientes', icon: Users, label: 'Clientes' },
    { path: '/ventas', icon: Receipt, label: 'Ventas' },
    { path: '/ofertas-laboratorio', icon: Percent, label: 'Ofertas' },
    { path: '/demanda-estacional', icon: TrendingUp, label: 'Demanda Estacional' },
    { path: '/sugerencias', icon: ShoppingCart, label: 'Sugerencias de Compra' },
    { path: '/etl', icon: Database, label: 'ETL' },
  ];

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Overlay para móvil cuando sidebar está abierto */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`bg-blue-900 text-white transition-all duration-300 z-50
          ${isMobile ? 'fixed h-full' : 'relative'}
          ${sidebarOpen ? 'w-64' : isMobile ? 'w-0 -translate-x-full' : 'w-20'}
        `}
      >
        <div className="p-4 flex items-center justify-between">
          <h1 className={`font-bold text-xl ${!sidebarOpen && 'hidden'}`}>
            SmartPharm
          </h1>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className={`p-2 rounded hover:bg-blue-800 ${!sidebarOpen && isMobile ? 'hidden' : ''}`}
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        <nav className={`mt-8 ${!sidebarOpen && isMobile ? 'hidden' : ''}`}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center px-4 py-3 hover:bg-blue-800 transition-colors ${
                  isActive ? 'bg-blue-800 border-l-4 border-white' : ''
                }`}
              >
                <Icon size={20} />
                <span className={`ml-3 ${!sidebarOpen && 'hidden'}`}>
                  {item.label}
                </span>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="px-4 md:px-6 py-3 md:py-4 flex justify-between items-center">
            {/* Botón hamburguesa para móvil */}
            {isMobile && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 rounded hover:bg-gray-100 mr-2"
              >
                <Menu size={24} className="text-gray-700" />
              </button>
            )}
            <h2 className="text-lg md:text-2xl font-semibold text-gray-800 truncate">
              {isMobile ? 'SmartPharm' : 'Sistema de Gestión Farmacéutica'}
            </h2>
            <div className="flex items-center gap-2 md:gap-4">
              <div className="flex items-center gap-2 md:gap-3">
                {user?.picture && (
                  <img
                    src={user.picture}
                    alt={user.name}
                    className="w-8 h-8 rounded-full border-2 border-gray-200"
                  />
                )}
                <span className="hidden md:inline text-sm text-gray-700 font-medium">{user?.name || user?.email}</span>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1 md:gap-2 px-2 md:px-3 py-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                  title="Cerrar sesión"
                >
                  <LogOut size={18} />
                  <span className="hidden md:inline text-sm font-medium">Cerrar Sesión</span>
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;