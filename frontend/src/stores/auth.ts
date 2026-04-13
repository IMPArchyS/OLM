import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiClient } from '@/lib/apiClient';
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
    const user = ref<User | null>(null);
    const providers = ref<OauthProvider[]>([]);
    const initialized = ref(false);
    let tokenRefreshInterval: ReturnType<typeof setInterval> | undefined = undefined;

    const setToken = (newAccessToken: string | null) => {
        accessToken.value = newAccessToken;
        if (newAccessToken) {
            const payload = parseJwt(newAccessToken);
            if (payload) {
                const parsedUserId = Number(payload.sub);
                const parsedRoleId = Number(payload.role_id);
                user.value = {
                    id: Number.isFinite(parsedUserId) ? parsedUserId : 0,
                    username: payload.username,
                    name: payload.name,
                    admin: payload.admin,
                    role_id: Number.isFinite(parsedRoleId) ? parsedRoleId : 0,
                };
            }
        } else {
            user.value = null;
        }
    };

    const startTokenRefresh = () => {
        tokenRefreshInterval = setInterval(
            () => {
                refreshAccessToken();
            },
            4 * 60 * 1000,
        );
    };

    const login = async (loginData: LoginForm) => {
        try {
            const response = await apiClient.post<AuthResponse>('auth/login', loginData);
            setToken(response.data.access_token);
            localStorage.setItem('OLMAccessToken', response.data.access_token);
            startTokenRefresh();
        } catch (err: any) {
            console.error('Login failed:', err);
            throw new Error(err.response?.data?.detail);
        }
    };

    const register = async (data: RegisterForm) => {
        try {
            const response = await apiClient.post<AuthResponse>('auth/register', data);
            setToken(response.data.access_token);
            localStorage.setItem('OLMAccessToken', response.data.access_token);
            startTokenRefresh();
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

    const logout = async () => {
        await apiClient
            .post('auth/logout')
            .then(() => {
                setToken(null);
                clearInterval(tokenRefreshInterval);
                localStorage.removeItem('OLMAccessToken');
            })
            .catch(() => {
                setToken(null);
            });
    };

    const refreshAccessToken = async () => {
        try {
            const response = await apiClient.post('auth/refresh');
            localStorage.setItem('OLMAccessToken', response.data.access_token);
            setToken(response.data.access_token);
        } catch (err) {
            console.log('Token refresh failed:', err);
            logout();
        }
    };

    const updateProfile = async (data: any): Promise<{ success: boolean; message?: string }> => {
        try {
            const response = await apiClient.patch<User>('auth/update-user', data);
            if (user.value) {
                user.value.name = response.data.name;
            }
            return { success: true };
        } catch (e: any) {
            console.error('Error updating user name:', e);
            return {
                success: false,
                message: e.response?.data?.message || 'Error updating user name',
            };
        }
    };

    const updatePassword = async (data: any): Promise<{ success: boolean; message?: string }> => {
        try {
            const response = await apiClient.patch<boolean>('auth/change-password', data);
            return { success: true };
        } catch (e: any) {
            console.error('Error updating user password:', e);
            return {
                success: false,
                message: e.response?.data?.message || 'Error updating user password',
            };
        }
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
            setToken(response.data.access_token);
            localStorage.setItem('OLMAccessToken', response.data.access_token);
        } catch (err) {
            console.log('Token refresh failed:', err);
            throw new Error('OAuth callback failed');
        }
    }

    const initAuth = async () => {
        await apiClient
            .post('auth/refresh')
            .then(async (response) => {
                setToken(response.data.access_token);
                startTokenRefresh();
            })
            .catch((err) => {
                console.error('Token refresh failed:', err);
            });

        initialized.value = true;
    };

    return {
        accessToken,
        user,
        providers,
        initAuth,
        login,
        register,
        logout,
        updateProfile,
        updatePassword,
        fetchProviders,
        oauthLogin,
        handleOAuthCallback,
    };
});
