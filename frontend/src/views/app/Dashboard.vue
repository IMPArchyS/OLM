<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import type { Device, DeviceType, Reservation } from '@/types/api';
import { apiClient } from '@/lib/apiClient';
import ExperimentSandbox from '@/components/experiments/ExperimentSandbox.vue';

const { t } = useI18n();
const router = useRouter();

const reservations = ref<Reservation[]>([]);
const loading = ref(true);
const currentTime = ref(new Date());
const resolvingCameraTarget = ref(false);
const cameraDeviceName = ref('');
const cameraServerId = ref(0);
const reservationDeviceType = ref<DeviceType | null>(null);

let refreshInterval: number | null = null;
let reservationRefreshInterval: number | null = null;

const now = computed(() => currentTime.value);

// Find active reservation (current time is between start and end)
const activeReservation = computed(() => {
    return reservations.value.find((reservation) => {
        const start = new Date(reservation.start);
        const end = new Date(reservation.end);
        return now.value >= start && now.value <= end;
    });
});

// Find next upcoming reservation
const nextReservation = computed(() => {
    const upcoming = reservations.value
        .filter((reservation) => new Date(reservation.start) > now.value)
        .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());
    return upcoming[0] || null;
});

const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
};

const goToReservations = () => {
    router.push('/app/reservations');
};

const fetchReservations = async () => {
    try {
        const response = await apiClient.get('/reservation/me');
        reservations.value = response.data;
    } catch (e) {
        console.error('Failed to fetch reservations:', e);
    }
};

const resolveCameraTarget = async (deviceId: number): Promise<void> => {
    if (!Number.isFinite(deviceId) || deviceId <= 0) {
        cameraDeviceName.value = '';
        cameraServerId.value = 0;
        reservationDeviceType.value = null;
        return;
    }

    resolvingCameraTarget.value = true;

    try {
        const response = await apiClient.get<Device>(`/device/${deviceId}/`);
        const device = response.data;
        cameraDeviceName.value = device.name;
        cameraServerId.value = device.server_id;
        reservationDeviceType.value = device.device_type ?? null;
    } catch (e) {
        console.error('Failed to resolve camera target from reservation device_id:', e);
        cameraDeviceName.value = '';
        cameraServerId.value = 0;
        reservationDeviceType.value = null;
    } finally {
        resolvingCameraTarget.value = false;
    }
};

watch(
    () => activeReservation.value?.device_id ?? null,
    (deviceId) => {
        if (!deviceId) {
            cameraDeviceName.value = '';
            cameraServerId.value = 0;
            reservationDeviceType.value = null;
            return;
        }

        void resolveCameraTarget(deviceId);
    },
    { immediate: true },
);

onMounted(async () => {
    loading.value = true;
    await fetchReservations();
    loading.value = false;

    // Keep active/next reservation visibility in sync with wall-clock time.
    refreshInterval = window.setInterval(() => {
        currentTime.value = new Date();
    }, 1000);

    // Pull reservation updates periodically so dashboard transitions without manual refresh.
    reservationRefreshInterval = window.setInterval(() => {
        void fetchReservations();
    }, 60000);
});

onUnmounted(() => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }

    if (reservationRefreshInterval) {
        clearInterval(reservationRefreshInterval);
    }
});
</script>

<template>
    <v-card elevation="4">
        <v-card-title class="bg-card-title dashboard-title-bar">
            <div class="dashboard-title-left">
                <v-icon icon="mdi-view-dashboard" class="mr-2" />
                <span>{{ t('nav.dashboard') }}</span>
            </div>
            <div v-if="activeReservation" class="dashboard-title-chips">
                <v-chip size="small" color="success" variant="tonal" prepend-icon="mdi-check-circle">
                    {{ t('dashboard.active_reservation') }}
                </v-chip>
                <v-chip size="small" color="success" variant="tonal" prepend-icon="mdi-clock-start">
                    {{ t('dashboard.started') }}: {{ formatDateTime(activeReservation.start) }}
                </v-chip>
                <v-chip size="small" color="success" variant="tonal" prepend-icon="mdi-clock-end">
                    {{ t('dashboard.ends') }}: {{ formatDateTime(activeReservation.end) }}
                </v-chip>
            </div>
            <div v-else-if="nextReservation" class="dashboard-title-chips">
                <v-chip size="small" color="info" variant="tonal" prepend-icon="mdi-clock-outline">
                    {{ t('dashboard.next_reservation') }}
                </v-chip>
                <v-chip size="small" color="info" variant="tonal" prepend-icon="mdi-clock-start">
                    {{ t('dashboard.starts') }}: {{ formatDateTime(nextReservation.start) }}
                </v-chip>
                <v-chip size="small" color="info" variant="tonal" prepend-icon="mdi-clock-end">
                    {{ t('dashboard.ends') }}: {{ formatDateTime(nextReservation.end) }}
                </v-chip>
            </div>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pt-0">
            <div v-if="loading" style="display: flex; justify-content: center; align-items: center; padding: 32px">
                <v-progress-circular indeterminate color="primary" size="64" />
            </div>
            <div v-else-if="activeReservation">
                <ExperimentSandbox
                    :key="activeReservation.id"
                    :reservation="activeReservation"
                    :device-type="reservationDeviceType"
                    :camera-device-name="cameraDeviceName"
                    :camera-server-id="cameraServerId"
                    :resolving-camera-target="resolvingCameraTarget"
                />
            </div>
            <div v-else-if="nextReservation" class="dashboard-waiting">
                <v-icon icon="mdi-timer-sand" size="52" color="info" class="mb-3" />
                <p class="text-h6 mb-2">{{ t('dashboard.waiting_title') }}</p>
                <p class="text-body-1 text-medium-emphasis">{{ t('dashboard.waiting_body') }}</p>
            </div>
            <div v-else class="dashboard-empty">
                <v-icon icon="mdi-calendar-blank-outline" size="52" color="on-surface-variant" class="mb-3" />
                <p class="text-h6 mb-2">{{ t('dashboard.no_reservations') }}</p>
                <v-btn class="mt-2" color="primary" variant="elevated" prepend-icon="mdi-calendar-plus" @click="goToReservations">
                    {{ t('dashboard.create_reservation') }}
                </v-btn>
            </div>
        </v-card-text>
    </v-card>
</template>

<style scoped>
.dashboard-title-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    padding-block: 10px;
}

.dashboard-title-left {
    display: flex;
    align-items: center;
}

.dashboard-title-chips {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}

.dashboard-waiting,
.dashboard-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px 16px;
    text-align: center;
}
</style>
