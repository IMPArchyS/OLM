import { ref, computed } from 'vue'
import type { Device, Software } from '@/types/api'
import { apiClient } from './useAxios'

export function useDevices() {
    const devices = ref<Device[]>([])
    const loading = ref(false)
    const error = ref<string | null>(null)
    const deviceSoftwareMap = ref<Record<number, Software[]>>({})

    const devicesForSelect = computed(() => {
        return devices.value.map((device) => ({
            id: device.id,
            displayName: formatDeviceName(device),
        }))
    })

    function formatDeviceName(device: Device): string {
        const softwares = deviceSoftwareMap.value[device.id]
        if (softwares && softwares.length > 0) {
            const softwareNames = softwares.map((s) => s.name).join(', ')
            return `${device.name} - ${softwareNames}`
        }
        return device.name
    }

    function getDeviceById(deviceId: number): Device | undefined {
        return devices.value.find((d) => d.id === deviceId)
    }

    async function getDeviceByExperimentId(experimentId: number): Promise<Device | undefined> {
        try {
            const response = await apiClient.get(`/experiment/${experimentId}/device`)
            return response.data
        } catch (e) {
            console.error(`Error fetching device for experiment ${experimentId}:`, e)
            return undefined
        }
    }

    async function fetchDeviceSoftware(deviceId: number): Promise<void> {
        try {
            const response = await apiClient.get(`/device/${deviceId}/software`)
            deviceSoftwareMap.value[deviceId] = response.data
        } catch (e) {
            console.error(`Error fetching software for device ${deviceId}:`, e)
            deviceSoftwareMap.value[deviceId] = []
        }
    }

    async function fetchDevices(): Promise<void> {
        loading.value = true
        error.value = null

        try {
            const response = await apiClient.get('/device/')
            devices.value = response.data
            await Promise.all(devices.value.map((device) => fetchDeviceSoftware(device.id)))
        } catch (e) {
            console.error('Error fetching devices:', e)
            error.value = 'Error fetching devices'
            devices.value = []
        } finally {
            loading.value = false
        }
    }

    async function fetchDevicesByServer(serverId: number): Promise<void> {
        loading.value = true
        error.value = null

        try {
            const response = await apiClient.get(`/server/${serverId}/devices`)
            devices.value = response.data
            await Promise.all(devices.value.map((device) => fetchDeviceSoftware(device.id)))
        } catch (e) {
            console.error('Error fetching devices for server:', e)
            error.value = 'Error fetching devices'
            devices.value = []
        } finally {
            loading.value = false
        }
    }

    return {
        devices,
        devicesForSelect,
        loading,
        error,
        fetchDevices,
        fetchDevicesByServer,
        getDeviceById,
        getDeviceByExperimentId,
        deviceSoftwareMap,
    }
}
