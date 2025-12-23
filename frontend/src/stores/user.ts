// stores/user.ts
import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';

export interface User {
    username: string;
    email: string;
}

export const useUserStore = defineStore('user', () => {
    const user = ref<User | null>(null);
    const isLoggedIn = computed(() => user.value !== null);
    // Initialize user from localStorage
    const initUser = () => {
        const savedUser = localStorage.getItem('user');
        if (savedUser) {
            try {
                user.value = JSON.parse(savedUser);
            } catch (error) {
                console.error('Failed to parse user from localStorage:', error);
                localStorage.removeItem('user');
            }
        }
    };

    // Login (dummy function for now)
    const login = (username: string, email: string) => {
        user.value = { username, email };
        console.log('User logged in:', user.value);
        // TODO: Add actual login API call here
    };

    // Logout
    const logout = () => {
        user.value = null;
        localStorage.removeItem('user');
        console.log('User logged out');
        // TODO: Add actual logout API call here
    };

    const updateProfile = () => {
        console.log('update profile');
    };

    const updatePassword = () => {
        console.log('update password');
    };

    // Watch for user changes and persist
    watch(
        user,
        (newUser) => {
            if (newUser) {
                localStorage.setItem('user', JSON.stringify(newUser));
            }
        },
        { deep: true },
    );

    return {
        user,
        isLoggedIn,
        initUser,
        login,
        logout,
        updateProfile,
        updatePassword,
    };
});
