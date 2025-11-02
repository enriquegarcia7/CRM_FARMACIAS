import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para manejo de errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Servicios para Clientes
export const clientesService = {
  getAll: () => api.get('/clientes/'),
  getById: (id) => api.get(`/clientes/${id}/`),
  create: (data) => api.post('/clientes/', data),
  update: (id, data) => api.put(`/clientes/${id}/`, data),
  delete: (id) => api.delete(`/clientes/${id}/`),
  getFrecuentes: () => api.get('/clientes/frecuentes/'), // Endpoint a crear
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

// Servicios para Productos (a implementar en backend)
export const productosService = {
  getAll: () => api.get('/productos/'),
  getById: (id) => api.get(`/productos/${id}/`),
  getLowStock: () => api.get('/productos/low-stock/'),
  getTopSelling: (limit = 10) => api.get(`/productos/top-selling/?limit=${limit}`),
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
  getProgress: () => api.get('/etl/progress/')
};

// Servicios para Gmail OAuth
export const gmailAuthService = {
  checkStatus: () => api.get('/gmail/auth/status/'),
  startAuth: () => api.get('/gmail/auth/start/'),
  revokeAuth: () => api.delete('/gmail/auth/revoke/')
};

// Servicios para Autenticación de Usuario (Login con Google)
export const authService = {
  startLogin: () => api.get('/auth/login/start/'),
  checkSession: () => api.get('/auth/session/'),
  logout: () => api.post('/auth/logout/')
};

export default api;
