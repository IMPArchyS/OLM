import { authStore } from '@/main';
import axios from 'axios';

const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api',
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000,
    withCredentials: true,
});

const authClient = axios.create({
    baseURL: import.meta.env.VITE_AUTH_SERVICE_URL,
    headers: {
        'Content-Type': 'application/json',
        'x-api-key': import.meta.env.VITE_API_KEY,
    },
    timeout: 10000,
    withCredentials: true,
});

authClient.interceptors.request.use(
    (config) => {
        const token = authStore.accessToken;
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    },
);

export { apiClient, authClient };
