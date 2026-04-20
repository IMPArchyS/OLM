<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import type { Device, DeviceType, Reservation } from '@/types/api';
import { apiClient } from '@/lib/apiClient';
import ExperimentSandbox from '@/components/experiments/ExperimentSandbox.vue';
import { useServers } from '@/composables/useServers';
import { useDevices } from '@/composables/useDevices';

const { t } = useI18n();
const router = useRouter();

const reservations = ref<Reservation[]>([]);
const loading = ref(true);
const currentTime = ref(new Date());
const resolvingCameraTarget = ref(false);
const cameraDeviceName = ref('');
const cameraServerId = ref(0);
const reservationDeviceType = ref<DeviceType | null>(null);

const { servers, fetchServers } = useServers();
const { devices, fetchDevicesByServer, fetchDevices } = useDevices();

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
        let matchedDevice: Device | null = null;

        if (servers.value.length === 0) {
            await fetchServers();
        }

        for (const server of servers.value) {
            await fetchDevicesByServer(server.id);
            const candidate = devices.value.find((device) => device.id === deviceId);

            if (candidate) {
                matchedDevice = candidate;
                cameraDeviceName.value = matchedDevice.name;
                cameraServerId.value = server.id;
                break;
            }
        }

        if (!matchedDevice) {
            cameraDeviceName.value = '';
            cameraServerId.value = 0;
            reservationDeviceType.value = null;
            return;
        }

        reservationDeviceType.value = matchedDevice.device_type ?? null;
        if (reservationDeviceType.value?.visual_config) {
            return;
        }

        const listFetchResult = await fetchDevices();
        if (listFetchResult.success) {
            const fromAllDevices = devices.value.find((device) => device.id === deviceId);
            if (fromAllDevices?.device_type) {
                reservationDeviceType.value = fromAllDevices.device_type;
            }
        }

        if (reservationDeviceType.value?.visual_config) {
            return;
        }

        const response = await apiClient.get<Device>(`/device/${deviceId}/`);
        reservationDeviceType.value = response.data.device_type ?? reservationDeviceType.value;
    } catch (e) {
        console.error('Failed to resolve camera target from reservation device_id:', e);
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
    <v-card>
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ t('dashboard.title') }}</span>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
            <div v-if="loading" style="display: flex; justify-content: center; align-items: center; padding: 32px">
                <v-progress-circular indeterminate color="primary" size="64" />
            </div>
            <div v-else class="dashboard-content">
                <div v-if="activeReservation">
                    <v-alert type="success" variant="tonal" density="compact" class="dashboard-reservation-alert">
                        <div class="dashboard-reservation-row">
                            <span class="text-body-2 font-weight-medium">{{ t('dashboard.active_reservation') }}</span>
                            <div class="dashboard-reservation-meta">
                                <v-chip size="small" variant="text" prepend-icon="mdi-clock-start">
                                    {{ t('dashboard.started') }}: {{ formatDateTime(activeReservation.start) }}
                                </v-chip>
                                <v-chip size="small" variant="text" prepend-icon="mdi-clock-end">
                                    {{ t('dashboard.ends') }}: {{ formatDateTime(activeReservation.end) }}
                                </v-chip>
                            </div>
                        </div>
                    </v-alert>
                    <ExperimentSandbox
                        :key="activeReservation.id"
                        :reservation="activeReservation"
                        :device-type="reservationDeviceType"
                        :camera-device-name="cameraDeviceName"
                        :camera-server-id="cameraServerId"
                        :resolving-camera-target="resolvingCameraTarget"
                    />
                </div>
                <v-alert v-else-if="nextReservation" type="info" variant="tonal" density="compact" class="dashboard-reservation-alert">
                    <div class="dashboard-reservation-row">
                        <span class="text-body-2 font-weight-medium">{{ t('dashboard.next_reservation') }}</span>
                        <div class="dashboard-reservation-meta">
                            <v-chip size="small" variant="text" prepend-icon="mdi-clock-start">
                                {{ t('dashboard.starts') }}: {{ formatDateTime(nextReservation.start) }}
                            </v-chip>
                            <v-chip size="small" variant="text" prepend-icon="mdi-clock-end">
                                {{ t('dashboard.ends') }}: {{ formatDateTime(nextReservation.end) }}
                            </v-chip>
                        </div>
                    </div>
                </v-alert>
                <div v-else style="text-align: center; padding: 32px 0">
                    <p style="font-size: 18px; margin-bottom: 16px">
                        {{ t('dashboard.no_reservations') }}
                    </p>
                    <v-btn @click="goToReservations" color="primary" variant="elevated">
                        {{ t('dashboard.create_reservation') }}
                    </v-btn>
                </div>
            </div>
        </v-card-text>
    </v-card>
</template>

<style scoped>
.dashboard-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.dashboard-reservation-alert {
    margin-bottom: 2px;
}

.dashboard-reservation-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    flex-wrap: wrap;
}

.dashboard-reservation-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}
</style>
