<script setup lang="ts">
import DeviceReservationCalendar from '@/components/DeviceReservationCalendar.vue';
import { useDevices } from '@/composables/useDevices';
import { useToast } from '@/composables/useToast';
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const { showError } = useToast();

const selectedDevice = ref<number | null>(null);

const { devicesForSelect, loading, fetchAvailableDevices, getDeviceById } = useDevices();

const selectedDeviceData = computed(() => {
    return selectedDevice.value ? getDeviceById(selectedDevice.value) : null;
});

onMounted(async () => {
    const result = await fetchAvailableDevices();
    if (!result.success) {
        showError(result.message || 'Failed');
    }
});
</script>

<template>
    <v-card class="mt-5">
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ t('reservations.title') }}</span>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
            <!-- Loading state -->
            <div v-if="loading" style="display: flex; justify-content: center; padding: 16px">
                <v-progress-circular indeterminate color="primary" size="48" />
            </div>

            <!-- Device Dropdown -->
            <v-select
                v-else
                v-model="selectedDevice"
                :items="devicesForSelect"
                item-title="displayName"
                item-value="id"
                :label="t('reservations.selectDevice')"
                :placeholder="t('reservations.chooseDevice')"
                variant="outlined"
                density="comfortable"
            />

            <!-- Calendar view  -->
            <div v-if="selectedDevice && selectedDeviceData" style="height: calc(100vh - 260px)">
                <DeviceReservationCalendar :selected-device-id="selectedDevice" :selected-device-data="selectedDeviceData" />
            </div>
        </v-card-text>
    </v-card>
</template>
