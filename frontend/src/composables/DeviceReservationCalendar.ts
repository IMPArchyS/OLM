import { ref, computed, watch } from 'vue'
import type { CalendarOptions, EventClickArg, DateSelectArg } from '@fullcalendar/core'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import listPlugin from '@fullcalendar/list'

export interface Device {
    id: number
    name: string
}

export interface Reservation {
    id: string
    deviceId: number
    title: string
    type: 'reservation' | 'maintenance'
    start: string // ISO datetime
    end: string // ISO datetime
    notes?: string
    userId?: string
}

export interface ReservationForm {
    deviceId: number
    title: string
    type: 'reservation' | 'maintenance'
    startDate: string
    endDate: string
    notes: string
}

interface Props {
    selectedDeviceId?: number | null
    selectedDeviceData?: Device | null
}

export function useDeviceReservationCalendar(props: Props) {
    const reservations = ref<Reservation[]>([])
    const loading = ref(false)

    const reservationModal = ref<HTMLDialogElement>()
    const editingReservation = ref<Reservation | null>(null)
    const fullCalendar = ref()

    const reservationForm = ref<ReservationForm>({
        deviceId: 0,
        title: '',
        type: 'reservation',
        startDate: '',
        endDate: '',
        notes: '',
    })

    // Fetch reservations from API
    async function fetchReservations() {
        if (!props.selectedDeviceId) return

        loading.value = true
        try {
            const response = await fetch(
                `http://localhost:8000/api/reservations/?device_id=${props.selectedDeviceId}`,
            )
            if (response.ok) {
                reservations.value = await response.json()
            }
        } catch (error) {
            console.error('Error fetching reservations:', error)
        } finally {
            loading.value = false
        }
    }

    // Watch for device changes and fetch reservations
    watch(
        () => props.selectedDeviceId,
        (newDeviceId) => {
            if (newDeviceId) {
                fetchReservations()
            } else {
                reservations.value = []
            }
        },
        { immediate: true },
    )

    // Convert reservations to FullCalendar events
    const calendarEvents = computed(() => {
        return reservations.value.map((r) => ({
            id: r.id,
            title: r.title,
            start: r.start,
            end: r.end,
            backgroundColor: r.type === 'maintenance' ? '#f87171' : '#34d399',
            borderColor: r.type === 'maintenance' ? '#dc2626' : '#10b981',
            extendedProps: {
                deviceId: r.deviceId,
                type: r.type,
                notes: r.notes,
                userId: r.userId,
            },
        }))
    })

    function handleDateSelect(selectInfo: DateSelectArg) {
        const calendarApi = selectInfo.view.calendar
        calendarApi.unselect()

        // Use selected device from parent
        if (!props.selectedDeviceId) return

        reservationForm.value = {
            deviceId: props.selectedDeviceId,
            title: '',
            type: 'reservation',
            startDate: formatDateTimeLocal(selectInfo.start),
            endDate: formatDateTimeLocal(selectInfo.end),
            notes: '',
        }

        editingReservation.value = null
        reservationModal.value?.showModal()
    }

    function handleEventClick(clickInfo: EventClickArg) {
        const event = clickInfo.event
        const reservation = reservations.value.find((r) => r.id === event.id)

        if (!reservation) return

        editingReservation.value = reservation
        reservationForm.value = {
            deviceId: reservation.deviceId,
            title: reservation.title,
            type: reservation.type,
            startDate: formatDateTimeLocal(new Date(reservation.start)),
            endDate: formatDateTimeLocal(new Date(reservation.end)),
            notes: reservation.notes || '',
        }

        reservationModal.value?.showModal()
    }

    async function saveReservation() {
        try {
            const reservationData = {
                device_id: reservationForm.value.deviceId,
                title: reservationForm.value.title,
                type: reservationForm.value.type,
                start: new Date(reservationForm.value.startDate).toISOString(),
                end: new Date(reservationForm.value.endDate).toISOString(),
                notes: reservationForm.value.notes,
            }

            if (editingReservation.value) {
                // Update existing
                const response = await fetch(
                    `http://localhost:8000/api/reservations/${editingReservation.value.id}/`,
                    {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(reservationData),
                    },
                )

                if (response.ok) {
                    await fetchReservations() // Refresh the list
                }
            } else {
                // Create new
                const response = await fetch('http://localhost:8000/api/reservations/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(reservationData),
                })

                if (response.ok) {
                    await fetchReservations() // Refresh the list
                }
            }

            updateCalendarEvents()
            closeModal()
        } catch (error) {
            console.error('Error saving reservation:', error)
            alert('Failed to save reservation')
        }
    }

    async function deleteReservation() {
        if (
            !editingReservation.value ||
            !confirm('Are you sure you want to delete this reservation?')
        ) {
            return
        }

        try {
            const response = await fetch(
                `http://localhost:8000/api/reservations/${editingReservation.value.id}/`,
                {
                    method: 'DELETE',
                },
            )

            if (response.ok) {
                await fetchReservations() // Refresh the list
                updateCalendarEvents()
                closeModal()
            }
        } catch (error) {
            console.error('Error deleting reservation:', error)
            alert('Failed to delete reservation')
        }
    }

    function updateCalendarEvents() {
        if (fullCalendar.value) {
            const calendarApi = fullCalendar.value.getApi()
            calendarApi.removeAllEvents()
            calendarApi.addEventSource(calendarEvents.value)
        }
    }

    function closeModal() {
        reservationModal.value?.close()
        editingReservation.value = null
    }

    function formatDateTimeLocal(date: Date): string {
        const year = date.getFullYear()
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        const hours = String(date.getHours()).padStart(2, '0')
        const minutes = String(date.getMinutes()).padStart(2, '0')
        return `${year}-${month}-${day}T${hours}:${minutes}`
    }

    // FullCalendar configuration
    const calendarOptions = computed<CalendarOptions>(() => ({
        plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin, listPlugin],
        initialView: 'timeGridWeek',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'timeGridDay,timeGridWeek,dayGridMonth,listWeek',
        },
        slotMinTime: '00:00:00',
        slotMaxTime: '24:00:00',
        allDaySlot: false,
        editable: false,
        selectable: true,
        selectMirror: true,
        dayMaxEvents: true,
        weekends: true,
        events: calendarEvents.value,
        select: handleDateSelect,
        eventClick: handleEventClick,
        height: 'auto',
        themeSystem: 'standard',
    }))

    return {
        reservations,
        reservationModal,
        editingReservation,
        fullCalendar,
        reservationForm,
        calendarOptions,
        calendarEvents,
        loading,
        fetchReservations,
        handleDateSelect,
        handleEventClick,
        saveReservation,
        deleteReservation,
        updateCalendarEvents,
        closeModal,
    }
}
