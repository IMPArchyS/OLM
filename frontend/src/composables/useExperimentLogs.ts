import type { ExperimentLog } from '@/types/api';
import { ref } from 'vue';
import { apiClient } from '../lib/apiClient';

export function useExperimentLogs() {
    const experimentLogs = ref<ExperimentLog[]>([]);
    const userExperimentLogs = ref<ExperimentLog[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);

    async function fetchExperimentLogs(): Promise<{ success: boolean; message?: string }> {
        loading.value = true;
        error.value = null;

        try {
            const response = await apiClient.get('/experiment_log');
            experimentLogs.value = response.data;
            return { success: true };
        } catch (e: any) {
            console.error('Error fetching experimentLogs:', e);
            experimentLogs.value = [];
            error.value = e.response?.data?.message || 'Failed to fetch available experimentLogs';
            return {
                success: false,
                message: error.value || 'Failed to fetch available experimentLogs',
            };
        } finally {
            loading.value = false;
        }
    }

    async function fetchExperimentLogsByUser(userId?: number): Promise<{ success: boolean; message?: string }> {
        loading.value = true;
        error.value = null;
        if (!userId) {
            error.value = 'Error fetching User id is Null';
            return {
                success: false,
                message: error.value || 'Error fetching User id is Null',
            };
        }
        try {
            const response = await apiClient.get(`/experiment_log/user/${userId}`);
            userExperimentLogs.value = response.data;
            return { success: true };
        } catch (e: any) {
            console.error('Error fetching userExperimentLogs:', e);
            userExperimentLogs.value = [];
            error.value = e.response?.data?.message || 'Failed to fetch available userExperimentLogs';
            return {
                success: false,
                message: error.value || 'Failed to fetch available userExperimentLogs',
            };
        } finally {
            loading.value = false;
        }
    }

    async function fetchLastUsedDeviceId(experimentId: number): Promise<number | null> {
        try {
            const response = await apiClient.get(`/experiment_log/${experimentId}/latest`);
            return response.data.device_id ?? null;
        } catch {
            return null;
        }
    }

    async function deleteExperimentLog(id: number): Promise<{ success: boolean; message?: string }> {
        try {
            await apiClient.delete(`/experiment_log/${id}`);
            return { success: true };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.detail || 'Failed to delete log' };
        }
    }

    async function restoreExperimentLog(id: number): Promise<{ success: boolean; message?: string }> {
        try {
            await apiClient.patch(`/experiment_log/${id}/restore`);
            return { success: true };
        } catch (e: any) {
            return { success: false, message: e.response?.data?.detail || 'Failed to restore log' };
        }
    }

    return {
        experimentLogs,
        userExperimentLogs,
        loading,
        error,
        fetchExperimentLogs,
        fetchExperimentLogsByUser,
        fetchLastUsedDeviceId,
        deleteExperimentLog,
        restoreExperimentLog,
    };
}
