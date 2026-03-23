import type { ExperimentLog } from '@/types/api';
import { ref } from 'vue';
import { apiClient } from './useAxios';

export function useExperimentLogs() {
    const experimentLogs = ref<ExperimentLog[]>([]);
    const userExperimentLogs = ref<ExperimentLog[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);

    async function fetchExperimentLogs(): Promise<{ success: boolean; message?: string }> {
        loading.value = true;

        try {
            const response = await apiClient.get('/experiment_log/');
            experimentLogs.value = response.data;
            return { success: true };
        } catch (e: any) {
            console.error('Error fetching experimentLogs:', e);
            experimentLogs.value = [];
            return {
                success: false,
                message: e.response?.data?.message || 'Failed to fetch available experimentLogs',
            };
        } finally {
            loading.value = false;
        }
    }

    async function fetchExperimentLogsByUser(userId?: number): Promise<{ success: boolean; message?: string }> {
        loading.value = true;
        if (!userId) {
            return {
                success: false,
                message: 'Error fetching User id is Null',
            };
        }
        try {
            const response = await apiClient.get(`/experiment_log/user/${userId}`);
            userExperimentLogs.value = response.data;
            return { success: true };
        } catch (e: any) {
            console.error('Error fetching userExperimentLogs:', e);
            userExperimentLogs.value = [];
            return {
                success: false,
                message: e.response?.data?.message || 'Failed to fetch available userExperimentLogs',
            };
        } finally {
            loading.value = false;
        }
    }

    return {
        experimentLogs,
        userExperimentLogs,
        loading,
        error,
        fetchExperimentLogs,
        fetchExperimentLogsByUser,
    };
}
