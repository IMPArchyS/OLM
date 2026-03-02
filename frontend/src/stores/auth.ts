import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiClient } from '@/composables/useAxios';
import router from '@/router';
import type { User, AuthResponse, OauthCredentials, OauthProvider } from '@/types/authTypes';
import type { LoginForm, RegisterForm } from '@/types/forms';

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
    const providers = ref<OauthProvider[]>([]);
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
            return true;
        } catch (err) {
            console.error('[AUTH]: INIT - Token refresh failed:', err);
            return false;
        }
    };

    const login = async (loginData: LoginForm): Promise<AuthResponse> => {
        try {
            const response = await apiClient.post<AuthResponse>('auth/login', loginData);
            const { access_token, refresh_token } = response.data;

            setTokens(access_token, refresh_token);
            startTokenRefresh();

            return response.data;
        } catch (err: any) {
            throw new Error(err.response?.data?.detail);
        }
    };

    const register = async (data: RegisterForm): Promise<AuthResponse> => {
        try {
            const response = await apiClient.post<AuthResponse>('auth/register', data);
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
            throw new Error(errorMessage);
        }
    };

    const refreshAccessToken = async () => {
        try {
            const response = await apiClient.post('auth/refresh');
            setToken(response.data.access_token);
        } catch (err) {
            console.log('Token refresh failed:', err);
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
                router.push('/auth/login');
            })
            .catch(() => {
                setToken(null);
                if (refreshIntervalId !== null) {
                    clearInterval(refreshIntervalId);
                    refreshIntervalId = null;
                }
                router.push('/auth/login');
            });
    };

    const fetchProviders = async (): Promise<void> => {
        try {
            const response = await apiClient.get('/auth/providers');
            providers.value = response.data;
        } catch (err) {
            console.error('Failed to fetch providers: ', err);
            providers.value = [];
        }
    };

    const oauthLogin = (credentials: OauthCredentials) => {
        const params = new URLSearchParams({
            provider: credentials.provider,
            redirect: credentials.redirect,
        });
        window.location.href = `${import.meta.env.VITE_AUTH_SERVICE_URL + '/api/auth/oauth/login'}?${params}`;
    };

    async function handleOAuthCallback() {
        try {
            const response = await apiClient.post('auth/session');
            setTokens(response.data.access_token, response.data.refresh_token);
        } catch (err) {
            console.log('Token refresh failed:', err);
            throw new Error('OAuth callback failed');
        }
    }

    return {
        accessToken,
        refreshToken,
        user,
        providers,
        initAuth,
        login,
        register,
        logout,
        fetchProviders,
        oauthLogin,
        handleOAuthCallback,
    };
});
