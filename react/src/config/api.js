// Configuración centralizada de la API
const API_CONFIG = {
  // Usar CloudFront para HTTPS (evita Mixed Content errors)
  // CloudFront hace proxy de /api/* hacia EC2 backend
  BASE_URL: 'http://localhost:8000',
  // BASE_URL: 'https://digheqbxnmxr3.cloudfront.net',
  API_VERSION: '/api/v1',
  TIMEOUT: 10000,
};

export const API_BASE = `${API_CONFIG.BASE_URL}${API_CONFIG.API_VERSION}`;

// Endpoints de la API
export const API_ENDPOINTS = {
  // Auth
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    ME: '/auth/me',
  },
  // Categories
  CATEGORIES: {
    BASE: '/categories',
    BY_ID: (id) => `/categories/${id}`,
  },
  // Products
  PRODUCTS: {
    BASE: '/products',
    BY_ID: (id) => `/products/${id}`,
    BY_codebar: (codebar) => `/products/codebar/${codebar}`,
    UPDATE_IMAGE: (id) => `/products/${id}/image`,
    UPDATE_STOCK: (id) => `/products/${id}/stock`,
  },
  // Orders
  ORDERS: {
    BASE: '/orders',
    ALL: '/orders/all',
    BY_ID: (id) => `/orders/${id}`,
    CART: '/orders/cart',
    CART_ITEM: (id) => `/orders/cart/${id}`,
    CHECKOUT: '/orders/checkout',
    UPDATE_STATUS: (id) => `/orders/${id}/status`,
    CANCEL: (id) => `/orders/${id}/cancel`,
  },
  // Admin
  ADMIN: {
    DASHBOARD: '/admin/dashboard',
    USERS: '/admin/users',
    USER_BY_ID: (id) => `/admin/users/${id}`,
  },
};

// Helper para construir URL completa
export const buildUrl = (endpoint, params = {}) => {
  let url = `${API_BASE}${endpoint}`;

  // Agregar query params si existen
  const queryString = new URLSearchParams(params).toString();
  if (queryString) {
    url += `?${queryString}`;
  }

  return url;
};

// Helper para obtener headers con token
export const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

export default API_CONFIG;