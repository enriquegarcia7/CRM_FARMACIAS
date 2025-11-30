import { useState, useEffect } from 'react';
import { Search, Mail, Star, User, TrendingUp, X, Send, Loader2 } from 'lucide-react';
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
    elegiblesOfertas: 0,
    sinCorreo: 0,
    correoInvalido: 0
  });

  // Estados para modal de oferta
  const [showOfertaModal, setShowOfertaModal] = useState(false);
  const [selectedCliente, setSelectedCliente] = useState(null);
  const [selectedDescuento, setSelectedDescuento] = useState(10);
  const [productosCliente, setProductosCliente] = useState([]);
  const [loadingProductos, setLoadingProductos] = useState(false);
  const [enviandoOferta, setEnviandoOferta] = useState(false);
  const [mensajeExito, setMensajeExito] = useState('');
  const [mensajeError, setMensajeError] = useState('');

  // Estados para modal masivo
  const [showMasivoModal, setShowMasivoModal] = useState(false);
  const [enviandoMasivo, setEnviandoMasivo] = useState(false);
  const [progresoEnvio, setProgresoEnvio] = useState({
    enviados: 0,
    total: 0,
    clienteActual: '',
    totalFrecuentes: 0,
    sinCorreo: 0,
    correoInvalido: 0,
    yaEnviados24h: 0
  });
  const [abortController, setAbortController] = useState(null);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [cancelado, setCancelado] = useState(false);

  const DESCUENTOS = [3, 5, 10, 15, 20];

  useEffect(() => {
    cargarEstadisticas();
    cargarClientes();
  }, [currentPage, tipoCliente]);

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
        elegiblesOfertas: response.data.elegibles_ofertas || 0,
        sinCorreo: response.data.sin_correo || 0,
        correoInvalido: response.data.correo_invalido || 0
      });
    } catch (error) {
      console.error('Error cargando estadísticas:', error);
    }
  };

  const cargarClientes = async () => {
    try {
      setLoading(true);
      setError(null);

      // Resetear página a 1 cuando cambia el filtro
      let response;

      if (tipoCliente === 'frecuentes') {
        // Usar endpoint específico para clientes frecuentes
        response = await clientesService.getFrecuentes({
          page: currentPage,
          page_size: pageSize
        });
      } else {
        // Consumir API paginada del backend
        response = await clientesService.getAll({
          page: currentPage,
          page_size: pageSize,
          tipo: tipoCliente // Pasar filtro al backend
        });
      }

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

    // Filtrar por término de búsqueda (solo local para búsqueda rápida)
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      resultado = resultado.filter(
        (c) =>
          (c.nombre && c.nombre.toLowerCase().includes(term)) ||
          (c.correo && c.correo.toLowerCase().includes(term))
      );
    }

    // NO filtrar por tipo aquí - ya viene filtrado del backend
    // El filtro tipoCliente se aplica en cargarClientes()

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

  // Abrir modal para envío individual
  const abrirModalOferta = async (cliente) => {
    setSelectedCliente(cliente);
    setSelectedDescuento(10);
    setMensajeExito('');
    setMensajeError('');
    setShowOfertaModal(true);
    setLoadingProductos(true);

    try {
      const response = await clientesService.getProductosComprados(cliente.id);
      setProductosCliente(response.data.productos || []);
    } catch (error) {
      console.error('Error cargando productos:', error);
      setProductosCliente([]);
    } finally {
      setLoadingProductos(false);
    }
  };

  // Enviar oferta individual
  const enviarOfertaIndividual = async () => {
    if (!selectedCliente) return;

    setEnviandoOferta(true);
    setMensajeExito('');
    setMensajeError('');

    try {
      const productosNombres = productosCliente.map(p => p.producto__nombre || p.producto__descripcion);
      const response = await clientesService.enviarOferta(selectedCliente.id, {
        descuento: selectedDescuento,
        productos: productosNombres
      });

      if (response.data.success) {
        setMensajeExito(`Oferta enviada exitosamente a ${selectedCliente.correo}`);
        setTimeout(() => {
          setShowOfertaModal(false);
          setMensajeExito('');
        }, 2000);
      } else {
        setMensajeError(response.data.error || 'Error al enviar la oferta');
      }
    } catch (error) {
      console.error('Error enviando oferta:', error);
      setMensajeError(error.response?.data?.error || 'Error al enviar la oferta. Verifica que Gmail esté autenticado.');
    } finally {
      setEnviandoOferta(false);
    }
  };

  // Abrir modal masivo
  const abrirModalMasivo = () => {
    setSelectedDescuento(10);
    setMensajeExito('');
    setMensajeError('');
    setShowMasivoModal(true);
  };

  // Enviar ofertas masivas con SSE para progreso en tiempo real
  const enviarOfertasMasivas = async () => {
    setEnviandoMasivo(true);
    setMensajeExito('');
    setMensajeError('');
    setCancelado(false);
    setProgresoEnvio({ enviados: 0, total: 0, clienteActual: '' });

    // Crear AbortController para poder cancelar
    const controller = new AbortController();
    setAbortController(controller);

    try {
      // Usar fetch con streaming para SSE (sin timeout)
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/clientes/enviar-ofertas-masivas/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ descuento: selectedDescuento }),
        signal: controller.signal
      });

      // Verificar si es SSE o JSON normal
      const contentType = response.headers.get('content-type');

      if (contentType && contentType.includes('text/event-stream')) {
        // Procesar SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value);
            const lines = text.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));

                  if (data.type === 'start') {
                    setProgresoEnvio(prev => ({
                      ...prev,
                      total: data.total,
                      totalFrecuentes: data.total_frecuentes || 0,
                      sinCorreo: data.sin_correo || 0,
                      correoInvalido: data.correo_invalido || 0,
                      yaEnviados24h: data.ya_enviados_24h || 0
                    }));
                  } else if (data.type === 'progress') {
                    setProgresoEnvio(prev => ({
                      ...prev,
                      enviados: data.enviados,
                      total: data.total,
                      clienteActual: data.cliente
                    }));
                  } else if (data.type === 'complete') {
                    setMensajeExito(`¡${data.enviados} ofertas enviadas exitosamente!`);
                    setTimeout(() => {
                      setShowMasivoModal(false);
                      setMensajeExito('');
                      setProgresoEnvio({ enviados: 0, total: 0, clienteActual: '', totalFrecuentes: 0, sinCorreo: 0, correoInvalido: 0, yaEnviados24h: 0 });
                    }, 3000);
                  } else if (data.type === 'error') {
                    setMensajeError(data.message);
                  }
                } catch (e) {
                  console.error('Error parsing SSE data:', e);
                }
              }
            }
          }
        } catch (readError) {
          if (readError.name === 'AbortError') {
            setCancelado(true);
            // No es un error, fue cancelado por el usuario
          } else {
            throw readError;
          }
        }
      } else {
        // Respuesta JSON normal (error)
        const data = await response.json();
        if (data.success) {
          setMensajeExito(`${data.enviados} ofertas enviadas exitosamente.`);
        } else {
          setMensajeError(data.error || 'Error al enviar las ofertas');
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        setCancelado(true);
        // Proceso cancelado por el usuario
      } else {
        console.error('Error enviando ofertas masivas:', error);
        setMensajeError('Error al enviar las ofertas. Verifica que Gmail esté autenticado.');
      }
    } finally {
      setEnviandoMasivo(false);
      setAbortController(null);
    }
  };

  // Función para solicitar cancelación
  const solicitarCancelacion = () => {
    setShowCancelConfirm(true);
  };

  // Función para confirmar cancelación
  const confirmarCancelacion = () => {
    if (abortController) {
      abortController.abort();
    }
    setShowCancelConfirm(false);
  };

  // Función para cerrar el modal (con o sin confirmación)
  const cerrarModalMasivo = () => {
    if (enviandoMasivo) {
      solicitarCancelacion();
    } else {
      setShowMasivoModal(false);
      setProgresoEnvio({ enviados: 0, total: 0, clienteActual: '' });
      setCancelado(false);
      setMensajeExito('');
      setMensajeError('');
    }
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
          onClick={abrirModalMasivo}
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
              <p className="text-xs text-gray-500 mt-1">≥5 compras + correo válido</p>
              {(stats.sinCorreo > 0 || stats.correoInvalido > 0) && (
                <div className="text-xs mt-2 space-y-1">
                  {stats.sinCorreo > 0 && (
                    <p className="text-gray-400">Sin correo: {stats.sinCorreo}</p>
                  )}
                  {stats.correoInvalido > 0 && (
                    <p className="text-yellow-600">Correo inválido: {stats.correoInvalido}</p>
                  )}
                </div>
              )}
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
              onChange={(e) => {
                setCurrentPage(1); // Resetear página al cambiar filtro
                setTipoCliente(e.target.value);
              }}
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
                        onClick={() => abrirModalOferta(cliente)}
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

      {/* Modal de Oferta Individual */}
      {showOfertaModal && selectedCliente && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-4 rounded-t-lg">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold">Enviar Oferta</h2>
                <button
                  onClick={() => setShowOfertaModal(false)}
                  className="text-white hover:text-gray-200"
                >
                  <X size={24} />
                </button>
              </div>
            </div>

            {/* Contenido */}
            <div className="p-6">
              {/* Preview del correo */}
              <div className="bg-gray-50 rounded-lg p-4 mb-4 border">
                <p className="text-gray-700">
                  Estimado Cliente <strong>{selectedCliente.nombre}</strong>,
                </p>
                <p className="text-gray-700 mt-2">
                  Gracias por su preferencia. Enviamos Oferta por el siguiente producto:
                </p>

                {/* Productos */}
                <div className="bg-white rounded p-3 mt-3 border">
                  {loadingProductos ? (
                    <div className="flex items-center justify-center py-2">
                      <Loader2 className="animate-spin mr-2" size={20} />
                      <span>Cargando productos...</span>
                    </div>
                  ) : productosCliente.length > 0 ? (
                    <ul className="list-disc list-inside text-gray-700">
                      {productosCliente.slice(0, 5).map((p, idx) => (
                        <li key={idx}>{p.producto__nombre || p.producto__descripcion}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-500 italic">Productos de su preferencia</p>
                  )}
                </div>

                {/* Descuento */}
                <div className="bg-green-500 text-white text-center font-bold py-3 rounded mt-4 text-xl">
                  {selectedDescuento}% DE DESCUENTO
                </div>

                {/* Pie */}
                <div className="mt-4 pt-3 border-t text-center text-gray-600">
                  <p><strong>Gracias</strong></p>
                  <p>Equipo de SmartPharm</p>
                </div>
              </div>

              {/* Selector de descuento */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Seleccionar % de Descuento:
                </label>
                <div className="flex gap-2 flex-wrap">
                  {DESCUENTOS.map((desc) => (
                    <button
                      key={desc}
                      onClick={() => setSelectedDescuento(desc)}
                      className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                        selectedDescuento === desc
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      {desc}%
                    </button>
                  ))}
                </div>
              </div>

              {/* Destinatario */}
              <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-600">
                  <strong>Enviar a:</strong> {selectedCliente.correo}
                </p>
              </div>

              {/* Mensajes */}
              {mensajeExito && (
                <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
                  {mensajeExito}
                </div>
              )}
              {mensajeError && (
                <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                  {mensajeError}
                </div>
              )}

              {/* Botones */}
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowOfertaModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={enviarOfertaIndividual}
                  disabled={enviandoOferta}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400"
                >
                  {enviandoOferta ? (
                    <>
                      <Loader2 className="animate-spin" size={18} />
                      Enviando...
                    </>
                  ) : (
                    <>
                      <Send size={18} />
                      Enviar Oferta
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Ofertas Masivas */}
      {showMasivoModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-4 rounded-t-lg">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold">Envío Masivo de Ofertas</h2>
                <button
                  onClick={cerrarModalMasivo}
                  className="text-white hover:text-gray-200"
                >
                  <X size={24} />
                </button>
              </div>
            </div>

            {/* Contenido */}
            <div className="p-6">
              {/* Mostrar resumen si fue cancelado */}
              {cancelado ? (
                <div className="mb-4">
                  <div className="bg-yellow-50 border border-yellow-400 rounded-lg p-4 mb-4">
                    <div className="flex items-center gap-2 text-yellow-800 mb-2">
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      <strong>Proceso cancelado</strong>
                    </div>
                    <p className="text-yellow-700">
                      Se enviaron <strong>{progresoEnvio.enviados}</strong> de <strong>{progresoEnvio.total}</strong> correos antes de cancelar.
                    </p>
                    <p className="text-yellow-700 text-sm mt-2">
                      Los clientes que ya recibieron oferta no serán incluidos si reinicia el proceso.
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setCancelado(false);
                      setProgresoEnvio({ enviados: 0, total: 0, clienteActual: '' });
                    }}
                    className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                  >
                    Reiniciar proceso con clientes restantes
                  </button>
                </div>
              ) : (
                <>
                  <div className="bg-purple-50 rounded-lg p-4 mb-4">
                    <p className="text-gray-700">
                      Se enviará una oferta personalizada a <strong>{stats.elegiblesOfertas} clientes frecuentes</strong> con sus productos más comprados.
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      (Excluye clientes que recibieron oferta en las últimas 24h)
                    </p>
                  </div>

                  {/* Selector de descuento */}
                  {!enviandoMasivo && (
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Seleccionar % de Descuento para todos:
                      </label>
                      <div className="flex gap-2 flex-wrap">
                        {DESCUENTOS.map((desc) => (
                          <button
                            key={desc}
                            onClick={() => setSelectedDescuento(desc)}
                            className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                              selectedDescuento === desc
                                ? 'bg-green-600 text-white'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                          >
                            {desc}%
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Preview o Progreso */}
                  {!enviandoMasivo ? (
                    <div className="bg-gray-50 rounded p-3 mb-4 border text-sm">
                      <p className="text-gray-600">Cada cliente recibirá un correo con:</p>
                      <ul className="list-disc list-inside text-gray-600 mt-2">
                        <li>Saludo personalizado con su nombre</li>
                        <li>Sus productos más comprados con comparativa de precios</li>
                        <li>{selectedDescuento}% de descuento con código único</li>
                        <li>Firma del Equipo SmartPharm</li>
                      </ul>
                    </div>
                  ) : (
                    <div className="mb-4">
                      {/* Contador grande */}
                      <div className="bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg p-6 text-white text-center mb-4">
                        <div className="text-5xl font-bold mb-2">
                          {progresoEnvio.enviados}
                          <span className="text-2xl font-normal opacity-75"> / {progresoEnvio.total}</span>
                        </div>
                        <div className="text-sm opacity-90">correos enviados</div>
                      </div>

                      {/* Barra de progreso */}
                      <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
                        <div
                          className="bg-gradient-to-r from-purple-500 to-blue-500 h-3 rounded-full transition-all duration-300"
                          style={{ width: `${progresoEnvio.total > 0 ? (progresoEnvio.enviados / progresoEnvio.total) * 100 : 0}%` }}
                        ></div>
                      </div>

                      {/* Cliente actual */}
                      {progresoEnvio.clienteActual && (
                        <div className="text-center text-sm text-gray-600 mb-3">
                          <span className="inline-flex items-center gap-2">
                            <Loader2 className="animate-spin" size={14} />
                            Enviando a: <strong>{progresoEnvio.clienteActual}</strong>
                          </span>
                        </div>
                      )}

                      {/* Resumen de excluidos */}
                      {(progresoEnvio.sinCorreo > 0 || progresoEnvio.correoInvalido > 0 || progresoEnvio.yaEnviados24h > 0) && (
                        <div className="bg-gray-100 rounded-lg p-3 text-xs text-gray-600">
                          <div className="font-medium mb-1">Clientes excluidos:</div>
                          <div className="flex flex-wrap gap-2">
                            {progresoEnvio.sinCorreo > 0 && (
                              <span className="bg-gray-200 px-2 py-1 rounded">
                                Sin correo: {progresoEnvio.sinCorreo}
                              </span>
                            )}
                            {progresoEnvio.correoInvalido > 0 && (
                              <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                                Correo inválido: {progresoEnvio.correoInvalido}
                              </span>
                            )}
                            {progresoEnvio.yaEnviados24h > 0 && (
                              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                Ya enviados (24h): {progresoEnvio.yaEnviados24h}
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Mensajes */}
                  {mensajeExito && (
                    <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded flex items-center gap-2">
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      {mensajeExito}
                    </div>
                  )}
                  {mensajeError && (
                    <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                      {mensajeError}
                    </div>
                  )}

                  {/* Botones */}
                  <div className="flex gap-3 justify-end">
                    {enviandoMasivo ? (
                      <button
                        onClick={solicitarCancelacion}
                        className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
                      >
                        Cancelar envío
                      </button>
                    ) : (
                      <>
                        <button
                          onClick={cerrarModalMasivo}
                          className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                        >
                          Cerrar
                        </button>
                        <button
                          onClick={enviarOfertasMasivas}
                          className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                        >
                          <Send size={18} />
                          Enviar a Todos
                        </button>
                      </>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal de confirmación de cancelación */}
      {showCancelConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-[60]">
          <div className="bg-white rounded-lg shadow-xl max-w-sm w-full mx-4 p-6">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100 mb-4">
                <svg className="h-6 w-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">¿Cancelar envío masivo?</h3>
              <p className="text-sm text-gray-500 mb-4">
                Se han enviado <strong>{progresoEnvio.enviados}</strong> de <strong>{progresoEnvio.total}</strong> correos.
                <br />
                Los correos ya enviados no se pueden deshacer.
              </p>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={() => setShowCancelConfirm(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Continuar enviando
                </button>
                <button
                  onClick={confirmarCancelacion}
                  className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
                >
                  Sí, cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Customers;
