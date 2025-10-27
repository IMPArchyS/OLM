<template>
    <div class="flex flex-col max-h-160! bg-base-100">
        <!-- Loading indicator -->
        <div v-if="loading" class="flex justify-center items-center p-8">
            <span class="loading loading-spinner loading-lg"></span>
        </div>

        <!-- FullCalendar -->
        <div v-else class="flex-1 p-4 overflow-auto">
            <FullCalendar ref="fullCalendar" :options="calendarOptions" />
        </div>

        <!-- Reservation Modal -->
        <dialog ref="reservationModal" class="modal">
            <div class="modal-box">
                <h3 class="font-bold text-lg mb-4">
                    {{ editingReservation ? 'Edit Reservation' : 'New Reservation' }}
                </h3>
                <!-- Debug info -->
                <div v-if="selectedDeviceData" class="text-xs text-base-content/60 mb-2">
                    Device ID: {{ selectedDeviceId }} | Name: {{ selectedDeviceData.name }}
                </div>
                <form @submit.prevent="saveReservation" class="space-y-4">
                    <div class="form-control">
                        <label class="label">
                            <span class="label-text">Device</span>
                        </label>
                        <input
                            :value="selectedDeviceData?.name || 'No device selected'"
                            type="text"
                            class="input input-bordered"
                            disabled
                        />
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Start Date</span>
                            </label>
                            <input
                                v-model="reservationForm.startDate"
                                type="datetime-local"
                                class="input input-bordered"
                                required
                            />
                        </div>

                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">End Date</span>
                            </label>
                            <input
                                v-model="reservationForm.endDate"
                                type="datetime-local"
                                class="input input-bordered"
                                required
                            />
                        </div>
                    </div>

                    <div class="modal-action">
                        <button
                            v-if="editingReservation"
                            type="button"
                            @click="deleteReservation"
                            class="btn btn-error"
                        >
                            Delete
                        </button>
                        <button type="button" @click="closeModal" class="btn">Cancel</button>
                        <button type="submit" class="btn btn-primary">Save</button>
                    </div>
                </form>
            </div>
            <form method="dialog" class="modal-backdrop">
                <button @click="closeModal">close</button>
            </form>
        </dialog>
    </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
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

onMounted(() => {
    updateCalendarEvents()
})
</script>

<style>
thead {
    background: var(--color-base-200) !important;
}
</style>
