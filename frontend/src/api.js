import axios from 'axios';

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token && token !== 'undefined' && token !== 'null') {
    if (config.headers.set) {
      config.headers.set('Authorization', `Bearer ${token}`);
    } else {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

API.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response && err.response.status === 401 && !err.config.url.includes('/auth/login')) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default API;
