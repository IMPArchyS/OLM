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
    <v-card>
        <v-card-title>
            {{ t('reservations.title') }}
        </v-card-title>
        <v-card-text>
            <!-- Device Dropdown -->
            <v-select
                v-model="selectedDevice"
                :items="devices"
                item-title="name"
                item-value="id"
                :label="t('reservations.selectDevice')"
                :placeholder="t('reservations.chooseDevice')"
                variant="outlined"
                density="comfortable"
            />

            <!-- Calendar view  -->
            <div v-if="selectedDevice && selectedDeviceData" style="height: calc(100vh - 260px)">
                <DeviceReservationCalendar
                    :selected-device-id="selectedDevice"
                    :selected-device-data="selectedDeviceData"
                />
            </div>
        </v-card-text>
    </v-card>
</template>
