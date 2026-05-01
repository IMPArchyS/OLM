import axios from 'axios';
import { authStore } from '@/main';
import router from '@/router';

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

apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        const status = error?.response?.status;
        if (status >= 500 && status !== 501) {
            router.push({ name: 'serverError' });
        }
        return Promise.reject(error);
    },
);

export { apiClient };
