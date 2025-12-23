<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ExperimentSandbox from '@/components/ExperimentSandbox.vue';
import type { Reservation } from '@/types/api';
import { apiClient } from '@/composables/useAxios';

const { t } = useI18n();
const router = useRouter();

const reservations = ref<Reservation[]>([]);
const loading = ref(true);
const currentTime = ref(new Date());
let refreshInterval: number | null = null;

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
        const response = await apiClient.get('/reservation/', {
            params: { queued: false },
        });
        reservations.value = response.data.filter(
            (reservation: Reservation) => !reservation.queued,
        );
    } catch (e) {
        console.error('Failed to fetch reservations:', e);
        reservations.value = [];
    }
};

onMounted(async () => {
    loading.value = true;
    await fetchReservations();
    loading.value = false;

    // Update current time every second for precise real-time updates
    refreshInterval = window.setInterval(() => {
        currentTime.value = new Date();
    }, 1000);

    // Refetch reservations every 5 minutes to get latest data
    window.setInterval(() => {
        fetchReservations();
    }, 300000);
});

onUnmounted(() => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});
</script>

<template>
    <v-card class="mt-5">
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ t('dashboard.title') }}</span>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
            <div
                v-if="loading"
                style="display: flex; justify-content: center; align-items: center; padding: 32px"
            >
                <v-progress-circular indeterminate color="primary" size="64" />
            </div>
            <div v-else style="display: flex; flex-direction: column; gap: 16px">
                <!-- Active Reservation -->
                <div v-if="activeReservation">
                    <v-alert type="success" variant="tonal">
                        <v-alert-title>{{ t('dashboard.active_reservation') }}</v-alert-title>
                        <div class="flex flex-row gap-3" style="margin-top: 8px">
                            <p>
                                <strong>{{ t('dashboard.started') }}:</strong>
                                {{ formatDateTime(activeReservation.start) }}
                            </p>
                            <p>
                                <strong>{{ t('dashboard.ends') }}:</strong>
                                {{ formatDateTime(activeReservation.end) }}
                            </p>
                        </div>
                    </v-alert>
                    <ExperimentSandbox :reservation="activeReservation" />
                </div>

                <!-- Next Reservation -->
                <v-alert v-else-if="nextReservation" type="info" variant="tonal">
                    <v-alert-title>{{ t('dashboard.next_reservation') }}</v-alert-title>
                    <div class="flex flex-row gap-3" style="margin-top: 8px">
                        <p>
                            <strong>{{ t('dashboard.starts') }}:</strong>
                            {{ formatDateTime(nextReservation.start) }}
                        </p>
                        <p>
                            <strong>{{ t('dashboard.ends') }}:</strong>
                            {{ formatDateTime(nextReservation.end) }}
                        </p>
                    </div>
                </v-alert>

                <!-- No Reservations -->
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
