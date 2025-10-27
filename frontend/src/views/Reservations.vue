<script setup lang="ts">
import DeviceReservationCalendar from '@/components/DeviceReservationCalendar.vue'
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Device {
    id: number
    name: string
}

const devices = ref<Device[]>([])
const selectedDevice = ref<number | null>(null)

const selectedDeviceData = computed(() => {
    return devices.value.find((device) => device.id === selectedDevice.value) || null
})

onMounted(async () => {
    const response = await fetch('http://localhost:8000/api/device/')
    if (response.ok) {
        devices.value = await response.json()
    }
})
</script>

<template>
    <div class="card bg-base-300! p-0! rounded-2xl!">
        <div class="card-header">
            <h2 class="text-xl font-semibold py-2.5! px-2.5!">{{ t('reservations.title') }}</h2>
        </div>
        <div class="card-body bg-base-200 rounded-b-2xl! px-2.5! pt-2! pb-4!">
            <!-- Device Dropdown -->
            <label for="device">{{ t('reservations.selectDevice') }}:</label>
            <select v-model="selectedDevice" id="device" class="select w-full bg-base-100! p-2!">
                <option disabled :value="null">{{ t('reservations.chooseDevice') }}</option>
                <option v-for="device in devices" :key="device.id" :value="device.id">
                    {{ device.name }}
                </option>
            </select>
            <!-- Calendar view  -->
            <div v-if="selectedDevice && selectedDeviceData" class="h-[calc(100vh-260px)]">
                <DeviceReservationCalendar
                    :selected-device-id="selectedDevice"
                    :selected-device-data="selectedDeviceData"
                />
            </div>
        </div>
    </div>
</template>
