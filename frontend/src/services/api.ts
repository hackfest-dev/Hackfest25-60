import axios from 'axios';

// Use window.location to dynamically determine the API base URL
const getBaseUrl = () => {
  const apiPath = '/api/v1';
  
  // If VITE_API_BASE_URL is available and not empty, use it
  if (import.meta.env.VITE_API_BASE_URL && import.meta.env.VITE_API_BASE_URL !== '/api/v1') {
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // In production with Docker, the backend and frontend will be on the same host
  // But frontend is on port 3000 and backend is on port 8001
  // So construct the URL dynamically
  return `${window.location.protocol}//${window.location.hostname}:8000${apiPath}`;
};

const API_BASE_URL = getBaseUrl();

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding the auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Authentication API calls
export const authAPI = {
  login: async (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    // Use the absolute URL through axios instance
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    if (response.data.access_token) {
      localStorage.setItem('accessToken', response.data.access_token);
    }
    
    return response.data;
  },
  
  signup: async (userData: {
    email: string;
    username: string;
    password: string;
    name: string;
  }) => {
    const response = await api.post('/auth/signup', userData);
    return response.data;
  },
  
  logout: async () => {
    const response = await api.post('/auth/logout');
    localStorage.removeItem('accessToken');
    return response.data;
  },
  
  isAuthenticated: () => {
    return localStorage.getItem('accessToken') !== null;
  },
  
  // Get current user profile
  getUserProfile: async () => {
    try {
      const response = await api.get('/users/me');
      return response.data;
    } catch (error) {
      console.error('Failed to get user profile:', error);
      return null;
    }
  },
  
  // Verify authentication
  verify: async () => {
    try {
      const response = await api.get('/auth/verify');
      return response.data;
    } catch (error) {
      console.error('Authentication verification failed:', error);
      return null;
    }
  }
};

// Orders API calls
export const ordersAPI = {
  // Shipper endpoints
  createOrder: async (orderData: {
    customer_name: string;
    customer_email: string;
    customer_phone: string;
    pickup_location: string;
    delivery_location: string;
    pickup_date: string;
    delivery_deadline: string;
    package_description: string;
    weight: number;
    dimensions?: string;
    total_amount: number;
    notes?: string;
    items: Array<{
      product_name: string;
      product_sku: string;
      quantity: number;
      unit_price: number;
    }>;
  }) => {
    const response = await api.post('/orders', orderData);
    return response.data;
  },
  
  getShipperOrders: async (page = 1, pageSize = 10, filters: {
    status?: string;
    customer_email?: string;
    is_assigned?: boolean;
    date_from?: string;
    date_to?: string;
  } = {}) => {
    const response = await api.get('/orders/my-shipments', { 
      params: { 
        page,
        page_size: pageSize,
        ...filters
      } 
    });
    return response.data;
  },
  
  // Carrier endpoints
  getAvailableOrders: async (page = 1, pageSize = 10) => {
    const response = await api.get('/orders/available', { 
      params: { 
        page,
        page_size: pageSize
      } 
    });
    return response.data;
  },
  
  getCarrierOrders: async (page = 1, pageSize = 10, filters: {
    status?: string;
    date_from?: string;
    date_to?: string;
  } = {}) => {
    const response = await api.get('/orders/my-deliveries', { 
      params: { 
        page,
        page_size: pageSize,
        ...filters
      } 
    });
    return response.data;
  },
  
  acceptOrder: async (orderId: number) => {
    const response = await api.post(`/orders/${orderId}/accept`);
    return response.data;
  },
  
  // Common endpoints
  getOrderById: async (orderId: number) => {
    const response = await api.get(`/orders/${orderId}`);
    return response.data;
  },
  
  trackOrder: async (trackingNumber: string) => {
    const response = await api.get(`/orders/track/${trackingNumber}`);
    return response.data;
  },
  
  updateOrderStatus: async (orderId: number, status: string) => {
    // Make sure status is uppercase to match backend expectations
    const statusValue = status.toUpperCase();
    console.log('Updating status to:', statusValue);
    const response = await api.patch(`/orders/${orderId}/status`, { status: statusValue });
    return response.data;
  },
};

export default api; 