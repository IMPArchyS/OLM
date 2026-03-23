import { ref, computed } from 'vue';
import type { Device } from '@/types/api';
import { apiClient } from './useAxios';

export function useDevices() {
    const devices = ref<Device[]>([]);
    const availableDevices = ref<Device[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);

    const devicesForReservation = computed(() => {
        return availableDevices.value.map((device) => ({
            id: device.id,
            displayName: device.name + ' | ' + device.softwares?.map((s) => s.name).join(', '),
        }));
    });

    function getAvailableDeviceById(deviceId: number): Device | undefined {
        return availableDevices.value.find((d) => d.id === deviceId);
    }

    async function fetchDevices(): Promise<{ success: boolean; message?: string }> {
        loading.value = true;

        try {
            const response = await apiClient.get('/device/');
            devices.value = response.data;
            return { success: true };
        } catch (e: any) {
            console.error('Error fetching devices:', e);
            devices.value = [];
            return {
                success: false,
                message: e.response?.data?.message || 'Failed to fetch available devices',
            };
        } finally {
            loading.value = false;
        }
    }

    async function fetchAvailableDevices(): Promise<{ success: boolean; message?: string }> {
        loading.value = true;

        try {
            const response = await apiClient.get('/device/available');
            availableDevices.value = response.data;
            return { success: true };
        } catch (e: any) {
            console.error('Error fetching available devices:', e);
            availableDevices.value = [];
            return {
                success: false,
                message: e.response?.data?.message || 'Failed to fetch available devices',
            };
        } finally {
            loading.value = false;
        }
    }

    async function fetchDevicesByServer(serverId: number): Promise<void> {
        loading.value = true;
        error.value = null;

        try {
            const response = await apiClient.get(`/server/${serverId}/devices`);
            devices.value = response.data;
        } catch (e) {
            console.error('Error fetching devices for server:', e);
            error.value = 'Error fetching devices';
            devices.value = [];
        } finally {
            loading.value = false;
        }
    }

    async function getDeviceByExperimentId(experimentId: number): Promise<Device | undefined> {
        try {
            const response = await apiClient.get(`/experiment/${experimentId}/device`);
            return response.data;
        } catch (e) {
            console.error(`Error fetching device for experiment ${experimentId}:`, e);
            return undefined;
        }
    }

    return {
        devices,
        devicesForReservation,
        loading,
        error,
        fetchDevices,
        fetchAvailableDevices,
        fetchDevicesByServer,
        getAvailableDeviceById,
        getDeviceByExperimentId,
    };
}
