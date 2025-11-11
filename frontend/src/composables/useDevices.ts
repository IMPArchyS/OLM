import { ref, computed } from 'vue'
import type { Device, Software } from '@/types/api'

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
            const response = await fetch(
                `http://localhost:8000/api/experiment/${experimentId}/device`,
            )

            if (response.ok) {
                const device: Device = await response.json()
                return device
            } else {
                console.error(`Failed to fetch device for experiment ${experimentId}`)
            }
        } catch (e) {
            console.error(`Error fetching device for experiment ${experimentId}:`, e)
        }
    }

    async function fetchDeviceSoftware(deviceId: number): Promise<void> {
        try {
            const response = await fetch(`http://localhost:8000/api/device/${deviceId}/software`)

            if (response.ok) {
                const softwares: Software[] = await response.json()
                deviceSoftwareMap.value[deviceId] = softwares
            } else {
                console.error(`Failed to fetch software for device ${deviceId}`)
                deviceSoftwareMap.value[deviceId] = []
            }
        } catch (e) {
            console.error(`Error fetching software for device ${deviceId}:`, e)
            deviceSoftwareMap.value[deviceId] = []
        }
    }

    async function fetchDevices(): Promise<void> {
        loading.value = true
        error.value = null

        try {
            const response = await fetch('http://localhost:8000/api/device/')

            if (response.ok) {
                const devicesData: Device[] = await response.json()
                devices.value = devicesData
                await Promise.all(devicesData.map((device) => fetchDeviceSoftware(device.id)))
            } else {
                error.value = `Failed to fetch devices: ${response.statusText}`
                devices.value = []
            }
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
            const response = await fetch(`http://localhost:8000/api/server/${serverId}/devices`)

            if (response.ok) {
                const devicesData: Device[] = await response.json()
                devices.value = devicesData

                // Fetch software for all devices
                await Promise.all(devicesData.map((device) => fetchDeviceSoftware(device.id)))
            } else {
                error.value = `Failed to fetch devices: ${response.statusText}`
                devices.value = []
            }
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
