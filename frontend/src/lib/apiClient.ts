import axios from 'axios';
import { authStore } from '@/main';

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000,
    withCredentials: true,
});

axios.defaults.withCredentials = true;

apiClient.interceptors.request.use(
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

export { apiClient };
