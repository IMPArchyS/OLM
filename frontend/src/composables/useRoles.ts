import type { Role } from '@/types/api';
import { ref } from 'vue';
import { authClient } from './useAxios';

export function useRoles() {
    const roles = ref<Role[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);

    async function fetchRoles(): Promise<void> {
        try {
            const response = await authClient.get('/internal/api/roles');
            roles.value = response.data;
            roles.value = roles.value.filter((r) => r.name.startsWith('olm'));
        } catch (e) {
            console.error('Failed to fetch roles:', e);
            roles.value = [];
        }
    }

    return {
        roles,
        loading,
        error,
        fetchRoles,
    };
}
