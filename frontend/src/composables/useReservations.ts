import { ref } from 'vue';
import { apiClient } from '@/lib/apiClient';
import type { Reservation } from '@/types/api';
import type { ReservationForm } from '@/types/forms';
import { useI18n } from 'vue-i18n';

export function useReservations() {
    const reservations = ref<Reservation[]>([]);
    const loading = ref(false);
    const { t } = useI18n();

    async function fetchReservations(deviceId?: number | null): Promise<{ success: boolean; message?: string }> {
        loading.value = true;

        try {
            const response = await apiClient.get('/reservation/', {
                params: deviceId ? { device_id: deviceId } : undefined,
            });

            reservations.value = response.data;
            return { success: true };
        } catch (fetchError: any) {
            console.error('Failed to fetch reservations:', fetchError);
            reservations.value = [];
            return { success: false, message: t('error.fetch') };
        } finally {
            loading.value = false;
        }
    }

    async function createReservation(reservationData: ReservationForm): Promise<{ success: boolean; message?: string }> {
        try {
            const response = await apiClient.post('/reservation/', reservationData);
            reservations.value.push(response.data);
            return { success: true };
        } catch (createError: any) {
            console.error('Error creating reservation:', createError);
            return { success: false, message: t('error.create') };
        }
    }

    async function updateReservation(reservationId: number, reservationData: ReservationForm): Promise<{ success: boolean; message?: string }> {
        try {
            await apiClient.patch(`/reservation/${reservationId}`, reservationData);
            const foundReservation = reservations.value.find((r) => r.id === reservationId);
            if (foundReservation) {
                foundReservation.start = reservationData.start;
                foundReservation.end = reservationData.end;
            }

            return { success: true };
        } catch (updateError: any) {
            console.error('Error updating reservation:', updateError);
            return { success: false, message: t('error.update') };
        }
    }

    async function deleteReservation(reservationId: number): Promise<{ success: boolean; message?: string }> {
        try {
            await apiClient.delete(`/reservation/${reservationId}`);
            reservations.value = reservations.value.filter((reservation) => reservation.id !== reservationId);
            return { success: true };
        } catch (deleteError: any) {
            console.error('Error deleting reservation:', deleteError);
            return { success: false, message: t('error.delete') };
        }
    }

    return {
        reservations,
        loading,
        fetchReservations,
        createReservation,
        updateReservation,
        deleteReservation,
    };
}
