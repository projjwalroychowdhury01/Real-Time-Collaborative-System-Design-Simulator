import axios from 'axios';
import { useAuthStore } from '@/store/uiStore';

const api = axios.create({ baseURL: '/api' });

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().setToken(null);
      window.location.href = '/login';
    }
    return Promise.reject(err);
  },
);

export default api;
