import { ref, computed, watch } from 'vue'
import type { CalendarOptions, EventClickArg, DateSelectArg } from '@fullcalendar/core'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import listPlugin from '@fullcalendar/list'
import skLocale from '@fullcalendar/core/locales/sk'
import { useI18n } from 'vue-i18n'
import type { Device, Reservation } from '@/types/api'
import type { ReservationForm } from '@/types/forms'

interface Props {
    selectedDeviceId?: number | null
    selectedDeviceData?: Device | null
}

export function useDeviceReservationCalendar(props: Props) {
    const reservations = ref<Reservation[]>([])
    const loading = ref(false)
    const { locale, t } = useI18n()

    const isModalOpen = ref(false)
    const editingReservation = ref<Reservation | null>(null)
    const fullCalendar = ref()

    const reservationForm = ref<ReservationForm>({
        deviceId: 0,
        startDate: '',
        endDate: '',
    })

    // Fetch reservations from API
    async function fetchReservations() {
        if (!props.selectedDeviceId) return

        loading.value = true
        try {
            const response = await fetch(
                `http://localhost:8000/api/reservation/?device_id=${props.selectedDeviceId}`,
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
            id: String(r.id),
            title: r.username || 'Reserved',
            start: r.start,
            end: r.end,
            extendedProps: {
                deviceId: r.device_id,
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
            startDate: formatDateTimeLocal(selectInfo.start),
            endDate: formatDateTimeLocal(selectInfo.end),
        }

        editingReservation.value = null
        isModalOpen.value = true
    }

    function handleEventClick(clickInfo: EventClickArg) {
        const event = clickInfo.event
        const reservation = reservations.value.find((r) => r.id === Number(event.id))

        if (!reservation) return

        // Check if event is in the past
        const eventEnd = new Date(reservation.end)
        const now = new Date()
        if (eventEnd < now) {
            alert('Cannot edit past reservations')
            return
        }

        editingReservation.value = reservation
        reservationForm.value = {
            deviceId: reservation.device_id,
            startDate: formatDateTimeLocal(new Date(reservation.start)),
            endDate: formatDateTimeLocal(new Date(reservation.end)),
        }

        isModalOpen.value = true
    }

    async function saveReservation() {
        try {
            const startDate = new Date(reservationForm.value.startDate)
            const endDate = new Date(reservationForm.value.endDate)

            const now = new Date()
            if (startDate < now || endDate < now) {
                alert('Cannot create reservation in the past')
                return
            }

            const reservationData = {
                device_id: reservationForm.value.deviceId,
                start: formatToISOLocal(startDate),
                end: formatToISOLocal(endDate),
            }

            if (editingReservation.value) {
                const response = await fetch(
                    `http://localhost:8000/api/reservation/${editingReservation.value.id}/`,
                    {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(reservationData),
                    },
                )

                if (!response.ok) {
                    const errorData = await response.json()
                    alert(
                        `Failed to update reservation: ${errorData.message || response.statusText}`,
                    )
                    return
                }

                await fetchReservations() // Refresh the list
            } else {
                // Create new
                const response = await fetch('http://localhost:8000/api/reservation/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(reservationData),
                })

                if (!response.ok) {
                    const errorData = await response.json()
                    alert(
                        `Failed to create reservation: ${errorData.message || response.statusText}`,
                    )
                    return
                }

                await fetchReservations() // Refresh the list
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
                `http://localhost:8000/api/reservation/${editingReservation.value.id}/`,
                {
                    method: 'DELETE',
                },
            )

            if (response.ok) {
                await fetchReservations()
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
        isModalOpen.value = false
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

    function formatToISOLocal(date: Date): string {
        const year = date.getFullYear()
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        const hours = String(date.getHours()).padStart(2, '0')
        const minutes = String(date.getMinutes()).padStart(2, '0')
        const seconds = String(date.getSeconds()).padStart(2, '0')
        return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
    }

    // FullCalendar configuration
    const calendarOptions = computed<CalendarOptions>(() => ({
        plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin, listPlugin],
        locale: locale.value === 'sk' ? skLocale : 'en',
        initialView: 'timeGridWeek',
        timeZone: 'local',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek',
        },
        buttonText: {
            today: t('calendar.today'),
            month: t('calendar.month'),
            week: t('calendar.week'),
            day: t('calendar.day'),
            list: t('calendar.list'),
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
        // Prevent clicking on past events
        eventAllow: (dropInfo, draggedEvent) => {
            const now = new Date()
            const eventStart = draggedEvent?.start
            return eventStart ? eventStart >= now : true
        },
        // Custom callback to check if event is in the past
        eventDidMount: (info) => {
            const eventEnd = info.event.end || info.event.start
            const now = new Date()
            if (eventEnd && eventEnd < now) {
                // Add visual indication for past events
                info.el.style.opacity = '0.6'
                info.el.style.cursor = 'not-allowed'
            }
        },
        height: '100%',
        themeSystem: 'standard',
        selectConstraint: {
            start: new Date().toISOString(),
        },
        stickyHeaderDates: true,
        stickyFooterScrollbar: true,
    }))

    return {
        reservations,
        isModalOpen,
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
