import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { authClient, setTokens, clearTokens, getAccessToken } from '@/composables/useAxios';

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

export const useAuthStore = defineStore('auth', () => {
    const isAuthenticated = ref(false);
    const isLoading = ref(false);
    const error = ref<string | null>(null);
    let refreshInterval: ReturnType<typeof setInterval> | null = null;

    const hasValidToken = computed(() => {
        return isAuthenticated.value && !!getAccessToken();
    });

    /**
     * Start automatic token refresh (every 4 minutes)
     */
    const startTokenRefresh = () => {
        // Clear any existing interval
        if (refreshInterval) {
            clearInterval(refreshInterval);
        }

        console.log('[Auth] Starting automatic token refresh (every 4 minutes)');
        // Refresh token every 4 minutes (240000ms)
        refreshInterval = setInterval(async () => {
            console.log('[Auth] Running automatic token refresh...');
            try {
                await refreshToken();
                console.log('[Auth] Token refreshed successfully');
            } catch (err) {
                console.error('[Auth] Auto token refresh failed:', err);
                // If refresh fails, logout user
                await logout();
            }
        }, 240000); // 4 minutes
    };

    /**
     * Stop automatic token refresh
     */
    const stopTokenRefresh = () => {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    };

    const refreshToken = async (): Promise<AuthResponse> => {
        try {
            console.log('[Auth] Attempting to refresh token...');

            const currentRefreshToken = localStorage.getItem('refresh_token');
            if (!currentRefreshToken) {
                throw new Error('No refresh token available');
            }

            // Call internal endpoint with refresh_token in body
            const response = await authClient.post<AuthResponse>('/refresh', {
                refresh_token: currentRefreshToken,
            });
            const { access_token, refresh_token } = response.data;

            setTokens(access_token, refresh_token);
            isAuthenticated.value = true;
            console.log('[Auth] Token refresh successful');

            return response.data;
        } catch (err: any) {
            console.error('[Auth] Token refresh failed:', err.response?.data || err.message);
            clearTokens();
            isAuthenticated.value = false;
            stopTokenRefresh();
            throw err;
        }
    };

    /**
     * Initialize auth - attempt to recover session from localStorage refresh token
     */
    const initAuth = async (): Promise<boolean> => {
        console.log('[Auth] Initializing auth...');
        // If already have a token in memory, we're good
        if (getAccessToken()) {
            console.log('[Auth] Found existing access token');
            isAuthenticated.value = true;
            startTokenRefresh();
            return true;
        }

        // Try to get a new access token using the refresh token from localStorage
        const refreshTokenValue = localStorage.getItem('refresh_token');
        if (refreshTokenValue) {
            try {
                console.log('[Auth] Found refresh token, attempting to restore session...');
                await refreshToken();
                startTokenRefresh();

                // Fetch current user data after successful session restoration
                try {
                    const accessToken = getAccessToken();
                    if (accessToken) {
                        const { useUserStore } = await import('@/stores/user');
                        const userStore = useUserStore();
                        await userStore.fetchCurrentUser(accessToken);
                        console.log('[Auth] User data restored');
                    }
                } catch (userErr) {
                    console.error('[Auth] Failed to fetch user data:', userErr);
                    // Continue anyway, user data can be fetched later if needed
                }

                return true;
            } catch (err) {
                // Refresh token is invalid or expired
                console.log('[Auth] Failed to restore session:', err);
                isAuthenticated.value = false;
                return false;
            }
        }

        // No valid session
        console.log('[Auth] No valid session found');
        isAuthenticated.value = false;
        return false;
    };

    /**
     * Login user
     */
    const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
        isLoading.value = true;
        error.value = null;

        try {
            const response = await authClient.post<AuthResponse>('/login', credentials);
            const { access_token, refresh_token } = response.data;

            setTokens(access_token, refresh_token);
            isAuthenticated.value = true;

            // Start automatic token refresh
            startTokenRefresh();

            return response.data;
        } catch (err: any) {
            const errorMessage =
                err.response?.data?.detail ||
                err.response?.data?.message ||
                err.response?.data?.error ||
                (typeof err.response?.data === 'string' ? err.response?.data : null) ||
                'Login failed';

            error.value = errorMessage;
            isAuthenticated.value = false;
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    /**
     * Register new user
     */
    const register = async (data: RegisterData): Promise<AuthResponse> => {
        isLoading.value = true;
        error.value = null;

        try {
            const response = await authClient.post<AuthResponse>('/register', data);
            const { access_token, refresh_token } = response.data;

            setTokens(access_token, refresh_token);
            isAuthenticated.value = true;

            // Start automatic token refresh
            startTokenRefresh();

            return response.data;
        } catch (err: any) {
            const errorMessage =
                err.response?.data?.detail ||
                err.response?.data?.message ||
                err.response?.data?.error ||
                (typeof err.response?.data === 'string' ? err.response?.data : null) ||
                'Registration failed';

            error.value = errorMessage;
            isAuthenticated.value = false;
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    /**
     * Logout user
     */
    const logout = async (): Promise<void> => {
        try {
            await authClient.post('/logout');
        } catch (err) {
            // Continue with logout even if API call fails
        } finally {
            stopTokenRefresh();
            clearTokens();
            isAuthenticated.value = false;

            // Clear user data
            try {
                const { useUserStore } = await import('@/stores/user');
                const userStore = useUserStore();
                userStore.clearUser();
            } catch (err) {
                console.error('[Auth] Failed to clear user data:', err);
            }
        }
    };

    /**
     * Clear error message
     */
    const clearError = () => {
        error.value = null;
    };

    return {
        isAuthenticated,
        isLoading,
        error,
        hasValidToken,
        initAuth,
        login,
        register,
        logout,
        refreshToken,
        clearError,
    };
});
