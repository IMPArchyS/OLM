import axios from 'axios';

const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api',
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000,
});

// Auth service client for external authentication
const authClient = axios.create({
    baseURL: import.meta.env.VITE_AUTH_SERVICE_URL,
    headers: {
        'Content-Type': 'application/json',
        'x-api-key': import.meta.env.VITE_API_KEY,
    },
    timeout: 10000,
});

let accessToken: string | null = null;

// Getters and setters for tokens
export const setTokens = (access: string, refresh: string) => {
    accessToken = access;
    // Store refresh token in localStorage so it persists across page refreshes
    localStorage.setItem('refresh_token', refresh);
};

export const getAccessToken = () => accessToken;

export const getRefreshToken = () => {
    // Try to get from localStorage if not in memory
    return localStorage.getItem('refresh_token');
};

export const clearTokens = () => {
    accessToken = null;
    localStorage.removeItem('refresh_token');
};

// Request interceptor for adding JWT token
apiClient.interceptors.request.use(
    (config) => {
        if (accessToken) {
            config.headers.Authorization = `Bearer ${accessToken}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    },
);

// Response interceptor for handling token refresh
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Don't retry on refresh endpoint (prevents infinite loop)
        const isRefreshRequest = originalRequest.url?.includes('/auth/refresh');

        // If 401 and we haven't retried yet and it's not the refresh endpoint
        if (error.response?.status === 401 && !originalRequest._retry && !isRefreshRequest) {
            originalRequest._retry = true;

            try {
                // Try to refresh the token
                const newAccessToken = await refreshAccessToken();
                if (newAccessToken) {
                    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                    return apiClient(originalRequest);
                }
            } catch (refreshError) {
                // Refresh failed, clear tokens and reject
                clearTokens();
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    },
);

// Function to refresh access token using internal endpoint
const refreshAccessToken = async (): Promise<string | null> => {
    try {
        const refreshToken = getRefreshToken();
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }

        // Call internal refresh endpoint with refresh_token in body
        const response = await authClient.post('/refresh', {
            refresh_token: refreshToken,
        });

        const { access_token, refresh_token: new_refresh_token } = response.data;
        setTokens(access_token, new_refresh_token);
        return access_token;
    } catch (error) {
        console.error('Failed to refresh token:', error);
        clearTokens();
        throw error;
    }
};

export { apiClient, authClient };
