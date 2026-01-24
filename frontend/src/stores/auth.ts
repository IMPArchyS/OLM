import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiClient, authClient } from '@/composables/useAxios';

interface LoginCredentials {
    username: string;
    password: string;
}

interface RegisterData {
    name: string;
    username: string;
    password: string;
}

interface AuthResponse {
    access_token: string;
    refresh_token: string;
    refresh_token_expires_at: string;
}

interface User {
    id: string;
    username: string;
    name: string;
    admin: boolean;
    role_id: number;
}

function parseJwt(token: string) {
    try {
        const base64Url = token.split('.')[1];
        if (!base64Url) {
            return null;
        }
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split('')
                .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join(''),
        );
        return JSON.parse(jsonPayload);
    } catch (e) {
        return null;
    }
}

export const useAuthStore = defineStore('auth', () => {
    const accessToken = ref<string | null>('');
    const refreshToken = ref<string | null>('');
    const user = ref<User | null>(null);
    const initialized = ref(false);
    let refreshIntervalId: number | null = null;

    const setToken = (newAccessToken: string | null, newRefreshToken?: string | null) => {
        accessToken.value = newAccessToken;
        if (newRefreshToken !== undefined) {
            refreshToken.value = newRefreshToken;
        }
        if (newAccessToken) {
            const payload = parseJwt(newAccessToken);
            if (payload) {
                user.value = {
                    id: payload.sub,
                    username: payload.username,
                    name: payload.name,
                    admin: payload.admin,
                    role_id: payload.role_id,
                };
            }
        } else {
            user.value = null;
        }
    };

    const setTokens = (newAccessToken: string | null, newRefreshToken: string | null) => {
        setToken(newAccessToken, newRefreshToken);
    };

    const initAuth = async (): Promise<boolean> => {
        try {
            const response = await apiClient.post('auth/refresh');
            setToken(response.data.access_token);
            startTokenRefresh();
            initialized.value = true;
            return true;
        } catch (err) {
            console.error('Token refresh failed:', err);
            initialized.value = true;
            return false;
        }
    };

    const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
        try {
            const response = await apiClient.post<AuthResponse>('auth/login', credentials);
            const { access_token, refresh_token } = response.data;

            setTokens(access_token, refresh_token);

            startTokenRefresh();

            return response.data;
        } catch (err: any) {
            const errorMessage =
                err.response?.data?.detail ||
                err.response?.data?.message ||
                err.response?.data?.error ||
                (typeof err.response?.data === 'string' ? err.response?.data : null) ||
                'Login failed';
            throw err;
        }
    };

    const register = async (data: RegisterData): Promise<AuthResponse> => {
        try {
            const response = await authClient.post<AuthResponse>('internal/api/register', data);
            const { access_token, refresh_token } = response.data;

            setTokens(access_token, refresh_token);

            startTokenRefresh();

            return response.data;
        } catch (err: any) {
            const errorMessage =
                err.response?.data?.detail ||
                err.response?.data?.message ||
                err.response?.data?.error ||
                (typeof err.response?.data === 'string' ? err.response?.data : null) ||
                'Registration failed';
            throw err;
        }
    };

    const refreshAccessToken = async () => {
        try {
            const response = await apiClient.post('auth/refresh');
            setToken(response.data.access_token);
        } catch (err) {
            console.error('Token refresh failed:', err);
            logout();
        }
    };

    const startTokenRefresh = () => {
        if (refreshIntervalId !== null) {
            clearInterval(refreshIntervalId);
        }
        refreshIntervalId = setInterval(
            () => {
                refreshAccessToken();
            },
            4 * 60 * 1000,
        );
    };

    const logout = async (): Promise<void> => {
        await apiClient
            .post('auth/logout')
            .then(() => {
                setToken(null);
                if (refreshIntervalId !== null) {
                    clearInterval(refreshIntervalId);
                    refreshIntervalId = null;
                }
            })
            .catch(() => {
                setToken(null);
            });
    };

    return {
        accessToken,
        refreshToken,
        user,
        initAuth,
        login,
        register,
        logout,
        startTokenRefresh,
        refreshAccessToken,
    };
});
