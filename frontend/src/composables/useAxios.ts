import axios from 'axios';

const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api',
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000,
});

// Request interceptor (optional - for auth tokens, etc.)
apiClient.interceptors.request.use(
    (config) => {
        // Add auth token if needed
        // const token = localStorage.getItem('token')
        // if (token) {
        //     config.headers.Authorization = `Bearer ${token}`
        // }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    },
);

// Response interceptor (optional - for error handling)
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        // Handle errors globally
        if (error.response?.status === 401) {
            // Handle unauthorized
        }
        return Promise.reject(error);
    },
);

export { apiClient };
