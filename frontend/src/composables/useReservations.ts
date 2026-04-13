import { ref } from 'vue';
import { apiClient } from '@/lib/apiClient';
import type { Reservation } from '@/types/api';
import type { ReservationForm } from '@/types/forms';

function getErrorMessage(error: any, fallback: string): string {
    return error?.response?.data?.message || error?.response?.data?.detail || fallback;
}

export function useReservations() {
    const reservations = ref<Reservation[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);

    async function hydrateReservationUsernames(reservationsData: Reservation[]): Promise<Reservation[]> {
        return Promise.all(
            reservationsData.map(async (reservation) => {
                try {
                    const userResponse = await apiClient.get(`/auth/user/${reservation.user_id}`);
                    return {
                        ...reservation,
                        username: userResponse.data.name,
                    };
                } catch (userError) {
                    console.error(`Error fetching user ${reservation.user_id}:`, userError);
                    return {
                        ...reservation,
                        username: 'Unknown User',
                    };
                }
            }),
        );
    }

    async function fetchReservations(deviceId?: number | null): Promise<{ success: boolean; message?: string }> {
        loading.value = true;
        error.value = null;

        try {
            const response = await apiClient.get('/reservation/', {
                params: deviceId ? { device_id: deviceId } : undefined,
            });

            reservations.value = await hydrateReservationUsernames(response.data);
            return { success: true };
        } catch (fetchError: any) {
            console.error('Failed to fetch reservations:', fetchError);
            reservations.value = [];
            error.value = getErrorMessage(fetchError, 'Failed to fetch reservations');
            return { success: false, message: error.value };
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
            return {
                success: false,
                message: getErrorMessage(createError, 'Failed to create reservation'),
            };
        }
    }

    async function updateReservation(reservationId: number, reservationData: ReservationForm): Promise<{ success: boolean; message?: string }> {
        try {
            await apiClient.patch(`/reservation/${reservationId}/`, reservationData);
            const foundReservation = reservations.value.find((r) => r.id === reservationId);
            if (foundReservation) {
                foundReservation.start = reservationData.start;
                foundReservation.end = reservationData.end;
            }

            return { success: true };
        } catch (updateError: any) {
            console.error('Error updating reservation:', updateError);
            return {
                success: false,
                message: getErrorMessage(updateError, 'Failed to update reservation'),
            };
        }
    }

    async function deleteReservation(reservationId: number): Promise<{ success: boolean; message?: string }> {
        try {
            await apiClient.delete(`/reservation/${reservationId}/`);
            reservations.value = reservations.value.filter((reservation) => reservation.id !== reservationId);
            return { success: true };
        } catch (deleteError: any) {
            console.error('Error deleting reservation:', deleteError);
            return {
                success: false,
                message: getErrorMessage(deleteError, 'Failed to delete reservation'),
            };
        }
    }

    return {
        reservations,
        loading,
        error,
        fetchReservations,
        createReservation,
        updateReservation,
        deleteReservation,
    };
}
