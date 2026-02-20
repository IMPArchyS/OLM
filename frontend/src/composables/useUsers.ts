import type { User } from '@/types/api';
import { ref } from 'vue';
import { authClient } from './useAxios';

export function useUsers() {
    const users = ref<User[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);
    const total = ref(0);
    const totalPages = ref(0);
    const userPage = ref(1);
    const userSize = ref(10);

    async function fetchUsers(page = 1, size = 10): Promise<void> {
        loading.value = true;
        error.value = null;
        try {
            const response = await authClient.get('/internal/api/users', {
                params: {
                    page,
                    size,
                },
            });
            const payload = response.data;
            if (Array.isArray(payload)) {
                users.value = payload;
                total.value = payload.length;
                totalPages.value = 1;
                userPage.value = page;
                userSize.value = size;
            } else {
                users.value = payload?.items ?? [];
                total.value = payload?.total ?? 0;
                totalPages.value = payload?.total_pages ?? 0;
                userPage.value = payload?.page ?? page;
                userSize.value = payload?.size ?? size;
            }
        } catch (e) {
            console.error('Failed to fetch users:', e);
            error.value = 'Failed to fetch users';
            users.value = [];
            total.value = 0;
            totalPages.value = 0;
        } finally {
            loading.value = false;
        }
    }

    return {
        users,
        loading,
        error,
        total,
        totalPages,
        userPage,
        userSize,
        fetchUsers,
    };
}
