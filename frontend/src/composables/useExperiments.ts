import type { Experiment } from '@/types/api';
import { ref } from 'vue';
import { apiClient } from './useAxios';

export function useExperiments() {
    const experiments = ref<Experiment[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);

    async function fetchExperiments(): Promise<{ success: boolean; message?: string }> {
        loading.value = true;

        try {
            const response = await apiClient.get('/experiment');
            experiments.value = response.data;
            return { success: true };
        } catch (e: any) {
            console.error('Error fetching experiments:', e);
            experiments.value = [];
            return {
                success: false,
                message: e.response?.data?.message || 'Failed to fetch available experiments',
            };
        } finally {
            loading.value = false;
        }
    }

    return {
        experiments,
        loading,
        error,
        fetchExperiments,
    };
}
