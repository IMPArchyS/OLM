<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ExperimentSandbox from '@/components/ExperimentSandbox.vue'

const { t } = useI18n()
const router = useRouter()

interface Reservation {
    id: number
    start: string
    end: string
    device_id: number
    username?: string
}

const reservations = ref<Reservation[]>([])
const loading = ref(true)
const currentTime = ref(new Date())
let refreshInterval: number | null = null

const now = computed(() => currentTime.value)

// Find active reservation (current time is between start and end)
const activeReservation = computed(() => {
    return reservations.value.find((reservation) => {
        const start = new Date(reservation.start)
        const end = new Date(reservation.end)
        return now.value >= start && now.value <= end
    })
})

// Find next upcoming reservation
const nextReservation = computed(() => {
    const upcoming = reservations.value
        .filter((reservation) => new Date(reservation.start) > now.value)
        .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
    return upcoming[0] || null
})

const formatDateTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    })
}

const goToReservations = () => {
    router.push('/app/reservations')
}

const fetchReservations = async () => {
    try {
        const response = await fetch('http://localhost:8000/api/reservation/')
        if (response.ok) {
            reservations.value = await response.json()
        } else {
            reservations.value = []
        }
    } catch (e) {
        console.error('Failed to fetch reservations:', e)
        reservations.value = []
    }
}

// onMounted(async () => {
//     loading.value = true
//     await fetchReservations()
//     loading.value = false

//     // Update current time every second for precise real-time updates
//     refreshInterval = window.setInterval(() => {
//         currentTime.value = new Date()
//     }, 1000)

//     // Refetch reservations every 5 minutes to get latest data
//     window.setInterval(() => {
//         fetchReservations()
//     }, 300000)
// })

// onUnmounted(() => {
//     if (refreshInterval) {
//         clearInterval(refreshInterval)
//     }
// })

// Dummy reservation for testing
const addDummyReservation = () => {
    loading.value = false
    const now = new Date()
    const dummyReservation: Reservation = {
        id: 999,
        start: new Date(now.getTime() - 10).toISOString(), // starts in 1 minute
        end: new Date(now.getTime() + 3600000).toISOString(), // ends in 1 hour
        device_id: 1,
        username: 'Test User',
    }
    reservations.value.push(dummyReservation)
}

onMounted(() => {
    reservations.value = []
    addDummyReservation()
})
</script>

<template>
    <div class="card bg-base-300! p-0! rounded-2xl!">
        <div class="card-header">
            <h2 class="text-xl font-semibold py-2.5! px-2.5!">{{ t('dashboard.title') }}</h2>
        </div>
        <div class="card-body bg-base-200 rounded-b-2xl! px-2.5! pt-2! pb-4!">
            <div v-if="loading" class="flex justify-center items-center p-8">
                <span class="loading loading-spinner loading-lg"></span>
            </div>
            <div v-else class="space-y-4">
                <!-- Active Reservation -->
                <div v-if="activeReservation">
                    <div class="flex flex-col gap-0 items-start alert alert-success">
                        <h3 class="text-lg text-white font-bold pl-1!">
                            {{ t('dashboard.active_reservation') }}
                        </h3>
                        <div class="text-sm text-white mb-2! pl-2!">
                            <p>
                                <strong>{{ t('dashboard.started') }}:</strong>
                                {{ formatDateTime(activeReservation.start) }}
                            </p>
                            <p>
                                <strong>{{ t('dashboard.ends') }}:</strong>
                                {{ formatDateTime(activeReservation.end) }}
                            </p>
                            <p v-if="activeReservation.username">
                                <strong>{{ t('dashboard.user') }}:</strong>
                                {{ activeReservation.username }}
                            </p>
                        </div>
                    </div>
                    <ExperimentSandbox :reservation="activeReservation" />
                </div>

                <!-- Next Reservation -->
                <div v-else-if="nextReservation" class="alert alert-info">
                    <div class="flex flex-col w-full">
                        <h3 class="text-lg text-white font-bold pl-1!">
                            {{ t('dashboard.next_reservation') }}
                        </h3>
                        <div class="text-sm text-white mb-2! pl-2!">
                            <p>
                                <strong>{{ t('dashboard.starts') }}:</strong>
                                {{ formatDateTime(nextReservation.start) }}
                            </p>
                            <p>
                                <strong>{{ t('dashboard.ends') }}:</strong>
                                {{ formatDateTime(nextReservation.end) }}
                            </p>
                            <p v-if="nextReservation.username">
                                <strong>{{ t('dashboard.user') }}:</strong>
                                {{ nextReservation.username }}
                            </p>
                        </div>
                    </div>
                </div>

                <!-- No Reservations -->
                <div v-else class="text-center py-8">
                    <p class="text-lg mb-4">{{ t('dashboard.no_reservations') }}</p>
                    <button @click="goToReservations" class="btn btn-primary">
                        {{ t('dashboard.create_reservation') }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
