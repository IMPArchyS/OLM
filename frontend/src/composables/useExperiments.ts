import type { Experiment } from '@/types/api';
import { ref } from 'vue';
import { apiClient } from './useAxios';
import type { QueueFormData } from '@/types/forms';

export function useExperiments() {
    const experiments = ref<Experiment[]>([]);
    const experimentsByDevice = ref<Experiment[]>([]);
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

    async function fetchExperimentsByDevice(deviceId: number): Promise<{ success: boolean; message?: string }> {
        loading.value = true;

        try {
            const response = await apiClient.get(`/experiment/device/${deviceId}`);
            experimentsByDevice.value = response.data;
            return { success: true };
        } catch (e: any) {
            console.error('Error fetching experimentsByDevice:', e);
            experimentsByDevice.value = [];
            return {
                success: false,
                message: e.response?.data?.message || 'Failed to fetch available experimentsByDevice',
            };
        } finally {
            loading.value = false;
        }
    }

    async function queueSelectedExperiment(experiment: QueueFormData): Promise<{ success: boolean; message?: string }> {
        loading.value = true;

        try {
            const response = await apiClient.post(`/experiment/queue`, experiment);
            return { success: true };
        } catch (e: any) {
            console.error('Error fetching experimentsByDevice:', e);
            return {
                success: false,
                message: e.response?.data?.message || 'Failed to fetch available experimentsByDevice',
            };
        } finally {
            loading.value = false;
        }
    }

    return {
        experiments,
        experimentsByDevice,
        loading,
        error,
        fetchExperiments,
        fetchExperimentsByDevice,
        queueSelectedExperiment,
    };
}
