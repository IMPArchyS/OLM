import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { authClient } from '@/composables/useAxios';

export interface User {
    id: number;
    name: string;
    username: string;
    admin: boolean;
    role_id: number;
}

export const useUserStore = defineStore('user', () => {
    const user = ref<User | null>(null);
    const isLoading = ref(false);
    const error = ref<string | null>(null);

    const isLoggedIn = computed(() => user.value !== null);

    const fetchCurrentUser = async (accessToken: string): Promise<void> => {
        isLoading.value = true;
        error.value = null;

        try {
            const response = await authClient.post<{ valid: boolean; user: User }>('/validate-token', {
                jwt_token: accessToken,
            });
            user.value = response.data.user;
        } catch (err: any) {
            error.value = err.response?.data?.message || 'Failed to fetch user data';
            console.error('Fetch current user error:', err);
            user.value = null;
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    const fetchUser = async (username: string): Promise<void> => {
        isLoading.value = true;
        error.value = null;

        try {
            const response = await authClient.get<User>(`/users/by-username/${username}`);
            user.value = response.data;
        } catch (err: any) {
            error.value = err.response?.data?.message || 'Failed to fetch user data';
            console.error('Fetch user error:', err);
            user.value = null;
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    const setUser = (userData: User) => {
        user.value = userData;
    };

    const clearUser = () => {
        user.value = null;
    };

    const updateProfile = async (profileData: Partial<User>): Promise<void> => {
        isLoading.value = true;
        error.value = null;

        try {
            const response = await authClient.patch<{ user: User }>('/profile', profileData);
            user.value = response.data.user;
            console.log('Profile updated:', user.value);
        } catch (err: any) {
            error.value = err.response?.data?.message || 'Profile update failed';
            console.error('Update profile error:', err);
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    const updatePassword = async (passwordData: { currentPassword: string; newPassword: string }): Promise<void> => {
        isLoading.value = true;
        error.value = null;

        try {
            await authClient.patch('/password', passwordData);
            console.log('Password updated successfully');
        } catch (err: any) {
            error.value = err.response?.data?.message || 'Password update failed';
            console.error('Update password error:', err);
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    const isAdmin = computed(() => user.value?.admin ?? false);

    return {
        user,
        isLoggedIn,
        isAdmin,
        isLoading,
        error,
        fetchCurrentUser,
        fetchUser,
        setUser,
        clearUser,
        updateProfile,
        updatePassword,
    };
});
