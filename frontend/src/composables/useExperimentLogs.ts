import type { ExperimentLog } from '@/types/api';
import { ref } from 'vue';
import { apiClient } from '../lib/apiClient';
import { useI18n } from 'vue-i18n';

export function useExperimentLogs() {
    const experimentLogs = ref<ExperimentLog[]>([]);
    const userExperimentLogs = ref<ExperimentLog[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);
    const { t } = useI18n();

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
            error.value = t('error.fetch');
            return { success: false, message: error.value };
        } finally {
            loading.value = false;
        }
    }

    async function fetchExperimentLogsByUser(): Promise<{ success: boolean; message?: string }> {
        error.value = null;
        loading.value = true;
        try {
            const response = await apiClient.get(`/experiment_log/me`);
            userExperimentLogs.value = response.data;
            return { success: true };
        } catch (e: any) {
            console.error('Error fetching userExperimentLogs:', e);
            userExperimentLogs.value = [];
            error.value = t('error.fetch');
            return { success: false, message: error.value };
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
            return { success: false, message: t('error.delete') };
        }
    }

    async function restoreExperimentLog(id: number): Promise<{ success: boolean; message?: string }> {
        try {
            await apiClient.patch(`/experiment_log/${id}/restore`);
            return { success: true };
        } catch (e: any) {
            return { success: false, message: t('error.restore') };
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
