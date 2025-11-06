import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 90000, // 90 segundos - timeout para solicitudes largas
});

// Interceptor para manejo de errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      console.error('API Timeout:', error);
      error.message = 'La solicitud tardó demasiado tiempo. El servidor puede estar procesando datos. Intenta recargar en unos momentos.';
    } else if (error.response) {
      console.error('API Error Response:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('API No Response:', error.request);
      error.message = 'No se pudo conectar con el servidor. Verifica que el backend esté ejecutándose.';
    } else {
      console.error('API Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Servicios para Clientes
export const clientesService = {
  getAll: (params = {}) => {
    // params: { page, page_size }
    const queryParams = new URLSearchParams();

    if (params.page) queryParams.append('page', params.page);
    if (params.page_size) queryParams.append('page_size', params.page_size);

    const queryString = queryParams.toString();
    return api.get(`/clientes/${queryString ? `?${queryString}` : ''}`);
  },
  getById: (id) => api.get(`/clientes/${id}/`),
  create: (data) => api.post('/clientes/', data),
  update: (id, data) => api.put(`/clientes/${id}/`, data),
  delete: (id) => api.delete(`/clientes/${id}/`),
  getFrecuentes: () => api.get('/clientes/frecuentes/'),
  getStats: () => api.get('/clientes/stats/'),
};

// Servicios para Transacciones
export const transaccionesService = {
  getAll: () => api.get('/transacciones/'),
  getById: (id) => api.get(`/transacciones/${id}/`),
  create: (data) => api.post('/transacciones/', data),
  update: (id, data) => api.put(`/transacciones/${id}/`, data),
  delete: (id) => api.delete(`/transacciones/${id}/`),
  getStats: () => api.get('/transacciones/stats/'), // Endpoint a crear
};

// Servicios para Productos
export const productosService = {
  getAll: (params = {}) => {
    // params: { page, page_size, search, filtro_stock }
    const queryParams = new URLSearchParams();

    if (params.page) queryParams.append('page', params.page);
    if (params.page_size) queryParams.append('page_size', params.page_size);
    if (params.search) queryParams.append('search', params.search);
    if (params.filtro_stock) queryParams.append('filtro_stock', params.filtro_stock);

    const queryString = queryParams.toString();
    return api.get(`/productos/${queryString ? `?${queryString}` : ''}`);
  },
  getById: (id) => api.get(`/productos/${id}/`),
  getLowStock: () => api.get('/productos/low-stock/'),
  getTopSelling: (limit = 10) => api.get(`/productos/top-selling/?limit=${limit}`),
  getUltimaCarga: () => api.get('/productos/ultima-carga/'),
  cargarExcel: (formData) => api.post('/productos/cargar_excel/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
};

// Servicios para Dashboard
export const dashboardService = {
  getStats: () => api.get('/dashboard/stats/'),
  getSalesData: () => api.get('/dashboard/sales/'),
  getTopProducts: (limit = 10) => api.get(`/dashboard/top-products/?limit=${limit}`),
};

// Servicios para Sugerencias de Compra (ML & Seasonality)
export const sugerenciasService = {
  getAll: () => api.get('/sugerencias/'),
  getByLowStock: () => api.get('/sugerencias/low-stock/'),
  getBySeason: () => api.get('/sugerencias/season/'),
  getByEpidemiological: () => api.get('/sugerencias/epidemiological/'),

  // MVP Purchase Optimizer Endpoints
  generar: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.limite) queryParams.append('limite', params.limite);
    if (params.forzar_mapeo !== undefined) queryParams.append('forzar_mapeo', params.forzar_mapeo);

    const queryString = queryParams.toString();
    return api.post(`/sugerencias/generar/${queryString ? `?${queryString}` : ''}`);
  },

  consolidar: () => api.get('/sugerencias/consolidar/'),

  exportExcel: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.proveedor) queryParams.append('proveedor', params.proveedor);

    const queryString = queryParams.toString();
    return api.get(`/sugerencias/export-excel/${queryString ? `?${queryString}` : ''}`, {
      responseType: 'blob'
    });
  },
};

// Servicios para Ofertas de Laboratorios (ETL)
export const ofertasService = {
  getAll: () => api.get('/ofertas/'),
  getPorLaboratorio: (params = {}) => {
    // params: { page, page_size, laboratorio, activas, search }
    const queryParams = new URLSearchParams();

    if (params.page) queryParams.append('page', params.page);
    if (params.page_size) queryParams.append('page_size', params.page_size);
    if (params.laboratorio) queryParams.append('laboratorio', params.laboratorio);
    if (params.search) queryParams.append('search', params.search);

    // Default activas = true
    const activas = params.activas !== undefined ? params.activas : true;
    queryParams.append('activas', activas);

    return api.get(`/ofertas/por_laboratorio/?${queryParams.toString()}`);
  },
  getLaboratorios: () => api.get('/ofertas/laboratorios/'),
  procesarArchivo: (formData) => api.post('/ofertas/procesar/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
};

// Servicios para ETL
export const etlService = {
  runManual: (daysBack = 5, strictMode = false) => api.post('/etl/run/', {
    days_back: daysBack,
    strict_mode: strictMode
  }),
  getLogs: () => api.get('/etl/logs/'),
  getStatus: () => api.get('/etl/status/'),
  getProgress: () => api.get('/etl/progress/'),
  getDiagnostic: (daysBack = 3) => api.get(`/etl/diagnostic/?days_back=${daysBack}`)
};

// Servicios para Gmail OAuth
export const gmailAuthService = {
  checkStatus: () => api.get('/gmail/auth/status/'),
  startAuth: () => api.get('/gmail/auth/start/'),
  revokeAuth: () => api.delete('/gmail/auth/revoke/')
};

// Servicios para Ventas
export const ventasService = {
  getAll: () => api.get('/ventas/'),
  getById: (id) => api.get(`/ventas/${id}/`),
  create: (data) => api.post('/ventas/', data),
  update: (id, data) => api.put(`/ventas/${id}/`, data),
  delete: (id) => api.delete(`/ventas/${id}/`),
  getStats: () => api.get('/ventas/stats/'),
};

// Servicios para Autenticación de Usuario (Login con Google)
export const authService = {
  startLogin: () => api.get('/auth/login/start/'),
  checkSession: () => api.get('/auth/session/'),
  logout: () => api.post('/auth/logout/')
};

export default api;
