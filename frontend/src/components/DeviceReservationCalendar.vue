<template>
    <div style="display: flex; flex-direction: column; height: 100%; overflow: hidden">
        <!-- Loading indicator -->
        <div
            v-if="loading"
            style="display: flex; justify-content: center; align-items: center; padding: 32px"
        >
            <v-progress-circular indeterminate color="primary" size="64" />
        </div>

        <!-- FullCalendar -->
        <div v-else style="flex: 1; padding: 16px; overflow: auto">
            <FullCalendar ref="fullCalendar" :options="calendarOptions" />
        </div>

        <!-- Reservation Modal -->
        <v-dialog v-model="isModalOpen" max-width="600px">
            <v-card>
                <v-card-title>
                    {{ editingReservation ? 'Edit Reservation' : 'New Reservation' }}
                </v-card-title>

                <!-- Debug info -->
                <v-card-subtitle v-if="selectedDeviceData" class="text-caption">
                    Device ID: {{ selectedDeviceId }} | Name: {{ selectedDeviceData.name }}
                </v-card-subtitle>

                <v-card-text>
                    <v-form @submit.prevent="saveReservation">
                        <v-row>
                            <v-col cols="12" md="6">
                                <v-text-field
                                    v-model="reservationForm.startDate"
                                    type="datetime-local"
                                    label="Start Date"
                                    variant="outlined"
                                    density="comfortable"
                                    required
                                />
                            </v-col>

                            <v-col cols="12" md="6">
                                <v-text-field
                                    v-model="reservationForm.endDate"
                                    type="datetime-local"
                                    label="End Date"
                                    variant="outlined"
                                    density="comfortable"
                                    required
                                />
                            </v-col>
                        </v-row>
                    </v-form>
                </v-card-text>

                <v-card-actions>
                    <v-btn color="grey" variant="text" @click="closeModal"> Cancel </v-btn>
                    <v-spacer />
                    <v-btn
                        v-if="editingReservation"
                        color="error"
                        variant="text"
                        @click="deleteReservation"
                    >
                        Delete
                    </v-btn>
                    <v-btn color="primary" variant="elevated" @click="saveReservation">
                        Save
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import { useDeviceReservationCalendar, type Device } from '../composables/DeviceReservationCalendar'

const props = defineProps<{
    selectedDeviceId?: number | null
    selectedDeviceData?: Device | null
}>()

const {
    reservationModal,
    editingReservation,
    fullCalendar,
    reservationForm,
    calendarOptions,
    loading,
    saveReservation,
    deleteReservation,
    updateCalendarEvents,
    closeModal,
} = useDeviceReservationCalendar(props)

// Control v-dialog with reactive state
const isModalOpen = ref(false)

// Watch the reservationModal ref to sync with v-dialog
watch(reservationModal, (modalElement) => {
    if (modalElement) {
        const observer = new MutationObserver(() => {
            isModalOpen.value = modalElement.hasAttribute('open')
        })
        observer.observe(modalElement, { attributes: true, attributeFilter: ['open'] })
    }
})

// Override closeModal to work with v-dialog
const closeModalVuetify = () => {
    isModalOpen.value = false
    closeModal()
}

// Update the composable's modal control
watch(isModalOpen, (newValue) => {
    if (newValue && reservationModal.value) {
        reservationModal.value.showModal()
    } else if (!newValue && reservationModal.value) {
        reservationModal.value.close()
    }
})

onMounted(() => {
    updateCalendarEvents()
})
</script>

<style>
/* thead {
    background: rgb(var(--v-theme-surface-variant)) !important;
} */
</style>
