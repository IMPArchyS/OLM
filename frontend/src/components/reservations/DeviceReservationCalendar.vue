<script setup lang="ts">
import { onMounted } from 'vue';
import FullCalendar from '@fullcalendar/vue3';
import { useDeviceReservationCalendar } from '@/composables/DeviceReservationCalendar';
import type { Device } from '@/types/api';

const props = defineProps<{
    selectedDeviceId?: number | null;
    selectedDeviceData?: Device | null;
}>();

const {
    isModalOpen,
    editingReservation,
    reservationForm,
    calendarOptions,
    loading,
    saveReservation,
    deleteReservation,
    updateCalendarEvents,
    closeModal,
} = useDeviceReservationCalendar(props);

onMounted(() => {
    updateCalendarEvents();
});
</script>

<template>
    <div style="display: flex; flex-direction: column; height: 100%; overflow: hidden">
        <div v-if="loading" style="display: flex; justify-content: center; align-items: center; padding: 32px">
            <v-progress-circular indeterminate color="primary" size="64" />
        </div>
        <div v-else style="flex: 1; padding: 16px; overflow: auto">
            <FullCalendar ref="fullCalendar" :options="calendarOptions" />
        </div>
        <v-dialog v-model="isModalOpen" max-width="600px">
            <v-card>
                <v-card-title>
                    {{ editingReservation ? $t('reservations.edit') : $t('reservations.new') }}
                </v-card-title>
                <v-card-text>
                    <v-form @submit.prevent="saveReservation">
                        <v-row>
                            <v-col cols="12" md="6">
                                <v-text-field
                                    v-model="reservationForm.start"
                                    type="datetime-local"
                                    label="Start Date"
                                    variant="outlined"
                                    density="comfortable"
                                    required
                                />
                            </v-col>

                            <v-col cols="12" md="6">
                                <v-text-field
                                    v-model="reservationForm.end"
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
                    <v-btn v-if="editingReservation" color="error" variant="text" @click="deleteReservation"> Delete </v-btn>
                    <v-btn color="primary" variant="elevated" @click="saveReservation"> Save </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<style>
thead {
    background: rgb(var(--v-theme-surface-variant)) !important;
}
</style>
