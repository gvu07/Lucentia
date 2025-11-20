import axios from 'axios';

const getDefaultApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    const isLocalhost = window.location.hostname === 'localhost';
    const host = isLocalhost ? '127.0.0.1' : window.location.hostname;
    const protocol = window.location.protocol === 'https:' ? 'https' : 'http';
    return `${protocol}://${host}:8000`;
  }
  return 'http://127.0.0.1:8000';
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || getDefaultApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = error.config?.url || '';
    const isAuthEndpoint =
      requestUrl.includes('/login') || requestUrl.includes('/register');

    if (error.response?.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/login', { email, password });
    return response.data;
  },
  
  register: async (email, password) => {
    const response = await api.post('/register', { email, password });
    return response.data;
  },
};

export const plaidAPI = {
  createLinkToken: async () => {
    const response = await api.post('/plaid/create_link_token');
    return response.data;
  },
  
  exchangeToken: async (publicToken) => {
    const response = await api.post('/plaid/exchange_token', { 
      public_token: publicToken
    });
    return response.data;
  },
};

export const dashboardAPI = {
  getDashboard: async () => {
    const response = await api.get('/dashboard');
    return response.data;
  },
  
  getInsights: async () => {
    const response = await api.get('/insights');
    return response.data;
  },
  
  getTransactions: async (limit = 100, offset = 0, startDate, endDate) => {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset)
    });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const response = await api.get(`/transactions?${params.toString()}`);
    return response.data;
  },
  
  getAccounts: async () => {
    const response = await api.get('/accounts');
    return response.data;
  },
};

export default api;
