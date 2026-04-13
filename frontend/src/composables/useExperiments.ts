import type { Experiment, Software } from '@/types/api';
import { ref } from 'vue';
import { apiClient } from '../lib/apiClient';
import type { CreateExperimentForm, EditExperimentForm, QueueFormData } from '@/types/forms';
import { Command } from '@/types/api';

export function useExperiments() {
    const experiments = ref<Experiment[]>([]);
    const experimentsByDevice = ref<Experiment[]>([]);
    const softwares = ref<Software[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);

    const defaultCommands: Command[] = [Command.INIT, Command.START, Command.CHANGE, Command.STOP];

    function normalizeExperiment(experiment: Experiment): Experiment {
        return {
            ...experiment,
            commands: experiment.commands?.length ? experiment.commands : defaultCommands,
            input_arguments: experiment.input_arguments || {},
            output_arguments: experiment.output_arguments || [],
            devices: experiment.devices || [],
        };
    }

    function normalizeExperiments(data: Experiment[]): Experiment[] {
        return data.map((experiment) => normalizeExperiment(experiment));
    }

    async function fetchExperiments(): Promise<{ success: boolean; message?: string }> {
        loading.value = true;

        try {
            const response = await apiClient.get('/experiment/');
            experiments.value = normalizeExperiments(response.data);
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
            experimentsByDevice.value = normalizeExperiments(response.data);
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

    async function getExperimentById(id: number): Promise<Experiment | null> {
        try {
            const response = await apiClient.get(`/experiment/${id}`);
            return normalizeExperiment(response.data);
        } catch (e) {
            console.error(`Error fetching experiment with id ${id}:`, e);
        }

        return null;
    }

    async function createExperiment(experiment: CreateExperimentForm): Promise<{ success: boolean; message?: string }> {
        try {
            const response = await apiClient.post('/experiment/', experiment);
            experiments.value.push(normalizeExperiment(response.data));
            return { success: true };
        } catch (e: any) {
            console.error('Error creating experiment:', e);
            return {
                success: false,
                message: e.response?.data?.detail || e.response?.data?.message || 'Failed to create experiment',
            };
        }
    }

    async function updateExperiment(experiment: EditExperimentForm): Promise<{ success: boolean; message?: string }> {
        try {
            const response = await apiClient.patch(`/experiment/${experiment.id}`, experiment);
            const index = experiments.value.findIndex((item) => item.id === experiment.id);

            if (index !== -1) {
                experiments.value[index] = normalizeExperiment(response.data);
            }

            return { success: true };
        } catch (e: any) {
            console.error('Error updating experiment:', e);
            return {
                success: false,
                message: e.response?.data?.detail || e.response?.data?.message || 'Failed to update experiment',
            };
        }
    }

    async function deleteExperiment(id: number): Promise<{ success: boolean; message?: string }> {
        try {
            await apiClient.delete(`/experiment/${id}`);
            await fetchExperiments();
            return { success: true };
        } catch (e: any) {
            console.error('Error deleting experiment:', e);
            return {
                success: false,
                message: e.response?.data?.detail || e.response?.data?.message || 'Failed to delete experiment',
            };
        }
    }

    async function restoreExperiment(id: number): Promise<{ success: boolean; message?: string }> {
        try {
            await apiClient.post(`/experiment/${id}/restore`);
            await fetchExperiments();
            return { success: true };
        } catch (e: any) {
            console.error('Error restoring experiment:', e);
            return {
                success: false,
                message: e.response?.data?.detail || e.response?.data?.message || 'Failed to restore experiment',
            };
        }
    }

    async function fetchSoftwares(): Promise<{ success: boolean; message?: string }> {
        loading.value = true;

        try {
            const response = await apiClient.get('/software/');
            softwares.value = response.data;
            return { success: true };
        } catch (e: any) {
            console.error('Error fetching softwares:', e);
            softwares.value = [];
            return {
                success: false,
                message: e.response?.data?.detail || e.response?.data?.message || 'Failed to fetch softwares',
            };
        } finally {
            loading.value = false;
        }
    }

    return {
        experiments,
        experimentsByDevice,
        softwares,
        defaultCommands,
        loading,
        error,
        fetchExperiments,
        fetchExperimentsByDevice,
        queueSelectedExperiment,
        getExperimentById,
        createExperiment,
        updateExperiment,
        deleteExperiment,
        restoreExperiment,
        fetchSoftwares,
    };
}
