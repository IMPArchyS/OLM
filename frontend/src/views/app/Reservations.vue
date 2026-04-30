<script setup lang="ts">
import DeviceReservationCalendar from '@/components/reservations/DeviceReservationCalendar.vue';
import { useDevices } from '@/composables/useDevices';
import { useToastStore } from '@/stores/toast';
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const toast = useToastStore();

const selectedDevice = ref<number | null>(null);

const { devicesForReservation, fetchAvailableDevices, getAvailableDeviceById } = useDevices();

const selectedDeviceData = computed(() => {
    return selectedDevice.value ? getAvailableDeviceById(selectedDevice.value) : null;
});

onMounted(async () => {
    const result = await fetchAvailableDevices();
    if (!result.success) toast.error(result.message || 'Failed');
});
</script>

<template>
    <v-card elevation="4">
        <v-card-title class="bg-card-title">
            <v-icon icon="mdi-calendar" class="mr-2" />
            <span>{{ t('nav.reservations') }}</span>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
            <v-select
                v-model="selectedDevice"
                :items="devicesForReservation"
                item-title="displayName"
                item-value="id"
                :label="t('reservations.selectDevice')"
                variant="outlined"
                density="compact"
            />
            <div v-if="selectedDevice && selectedDeviceData" style="height: calc(100vh - 260px)">
                <DeviceReservationCalendar :selected-device-id="selectedDevice" :selected-device-data="selectedDeviceData" />
            </div>
        </v-card-text>
    </v-card>
</template>
