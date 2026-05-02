import axios from 'axios';
const API = axios.create({ baseURL: 'http://localhost:8000/api' });

API.interceptors.request.use((config) => {
    const token = 'fake-token';
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

API.get('/health').then(res => {
    console.log('Headers sent:', res.config.headers);
}).catch(err => {
    console.error(err);
});
