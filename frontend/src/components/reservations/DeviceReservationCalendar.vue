<script setup lang="ts">
import FullCalendar from '@fullcalendar/vue3';
import { useDeviceReservationCalendar } from '@/composables/DeviceReservationCalendar';
import type { Device } from '@/types/api';

const props = defineProps<{
    selectedDeviceId?: number | null;
    selectedDeviceData?: Device | null;
}>();

const { isModalOpen, editingReservation, reservationForm, calendarOptions, loading, saveReservation, deleteReservation, closeModal } =
    useDeviceReservationCalendar(props);
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
                    {{ editingReservation ? $t('actions.edit') : $t('actions.create') }}
                </v-card-title>
                <v-card-text>
                    <v-form @submit.prevent="saveReservation">
                        <v-row>
                            <v-col cols="12" md="6">
                                <v-text-field
                                    v-model="reservationForm.start"
                                    type="datetime-local"
                                    :label="$t('reservations.startDate')"
                                    variant="outlined"
                                    density="comfortable"
                                    required
                                />
                            </v-col>

                            <v-col cols="12" md="6">
                                <v-text-field
                                    v-model="reservationForm.end"
                                    type="datetime-local"
                                    :label="$t('reservations.endDate')"
                                    variant="outlined"
                                    density="comfortable"
                                    required
                                />
                            </v-col>
                        </v-row>
                    </v-form>
                </v-card-text>

                <v-card-actions>
                    <v-btn prepend-icon="mdi-close" color="grey" variant="outlined" @click="closeModal"> {{ $t('actions.cancel') }} </v-btn>
                    <v-spacer />
                    <v-btn v-if="editingReservation" prepend-icon="mdi-trash-can" color="error" variant="outlined" @click="deleteReservation">
                        {{ $t('actions.delete') }}
                    </v-btn>
                    <v-btn prepend-icon="mdi-plus" color="primary" variant="elevated" @click="saveReservation"> {{ $t('actions.save') }} </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<style>
thead {
    background: rgb(var(--v-theme-surface-variant)) !important;
}

td {
    border-color: rgb(var(--v-theme-calendar)) !important;
}

tr {
    border-color: rgb(var(--v-theme-calendar)) !important;
}
</style>
