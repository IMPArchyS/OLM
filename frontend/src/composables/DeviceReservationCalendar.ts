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
import { apiClient } from './useAxios'

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

    async function fetchReservations() {
        if (!props.selectedDeviceId) return

        loading.value = true
        try {
            const response = await apiClient.get('/reservation/', {
                params: { device_id: props.selectedDeviceId },
            })
            reservations.value = response.data
        } catch (error) {
            console.error('Error fetching reservations:', error)
        } finally {
            loading.value = false
        }
    }

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

    const calendarEvents = computed(() => {
        const reservationEvents = reservations.value.map((r) => ({
            id: String(r.id),
            title: r.username || 'Reserved',
            start: r.start,
            end: r.end,
            backgroundColor: undefined,
            extendedProps: {
                deviceId: r.device_id,
                isMaintenance: false,
            },
        }))

        const maintenanceEvents = []
        if (
            props.selectedDeviceData?.maintenance_start &&
            props.selectedDeviceData?.maintenance_end
        ) {
            const today = new Date()
            for (let i = -365; i < 365; i++) {
                const eventDate = new Date(today)
                eventDate.setDate(today.getDate() + i)

                const maintenanceStart = props.selectedDeviceData.maintenance_start
                const maintenanceEnd = props.selectedDeviceData.maintenance_end

                const startParts = maintenanceStart.split(':').map(Number)
                const endParts = maintenanceEnd.split(':').map(Number)
                const startHour = startParts[0] ?? 0
                const startMinute = startParts[1] ?? 0
                const endHour = endParts[0] ?? 0
                const endMinute = endParts[1] ?? 0

                const startDateTime = new Date(eventDate)
                startDateTime.setHours(startHour, startMinute, 0, 0)

                const endDateTime = new Date(eventDate)
                endDateTime.setHours(endHour, endMinute, 0, 0)

                maintenanceEvents.push({
                    id: `maintenance-${i}`,
                    title: 'Maintenance',
                    start: startDateTime.toISOString(),
                    end: endDateTime.toISOString(),
                    backgroundColor: '#ef4444',
                    borderColor: '#dc2626',
                    extendedProps: {
                        deviceId: props.selectedDeviceData.id,
                        isMaintenance: true,
                    },
                })
            }
        }

        return [...reservationEvents, ...maintenanceEvents]
    })

    function handleDateSelect(selectInfo: DateSelectArg) {
        const calendarApi = selectInfo.view.calendar
        calendarApi.unselect()

        if (!props.selectedDeviceId) return

        if (
            props.selectedDeviceData?.maintenance_start &&
            props.selectedDeviceData?.maintenance_end
        ) {
            const startDate = selectInfo.start
            const endDate = selectInfo.end
            const maintenanceStart = props.selectedDeviceData.maintenance_start
            const maintenanceEnd = props.selectedDeviceData.maintenance_end

            const startParts = maintenanceStart.split(':').map(Number)
            const endParts = maintenanceEnd.split(':').map(Number)
            const maintenanceStartHour = startParts[0] ?? 0
            const maintenanceStartMinute = startParts[1] ?? 0
            const maintenanceEndHour = endParts[0] ?? 0
            const maintenanceEndMinute = endParts[1] ?? 0

            const currentDate = new Date(startDate)
            currentDate.setHours(0, 0, 0, 0) // Reset to start of day

            const endDateDay = new Date(endDate)
            endDateDay.setHours(23, 59, 59, 999) // Set to end of day

            while (currentDate <= endDateDay) {
                const dayMaintenanceStart = new Date(currentDate)
                dayMaintenanceStart.setHours(maintenanceStartHour, maintenanceStartMinute, 0, 0)

                const dayMaintenanceEnd = new Date(currentDate)
                dayMaintenanceEnd.setHours(maintenanceEndHour, maintenanceEndMinute, 0, 0)

                // Calculate the effective reservation period for this specific day
                const dayStart = new Date(currentDate)
                dayStart.setHours(0, 0, 0, 0)

                const dayEnd = new Date(currentDate)
                dayEnd.setHours(23, 59, 59, 999)

                // Get the overlap of reservation with this day
                const effectiveStart = startDate > dayStart ? startDate : dayStart
                const effectiveEnd = endDate < dayEnd ? endDate : dayEnd

                // Check if the effective reservation period on this day overlaps with maintenance
                if (
                    (effectiveStart >= dayMaintenanceStart && effectiveStart < dayMaintenanceEnd) ||
                    (effectiveEnd > dayMaintenanceStart && effectiveEnd <= dayMaintenanceEnd) ||
                    (effectiveStart <= dayMaintenanceStart && effectiveEnd >= dayMaintenanceEnd)
                ) {
                    alert(
                        `Cannot create reservation during maintenance period (${maintenanceStart} - ${maintenanceEnd})`,
                    )
                    return
                }

                currentDate.setDate(currentDate.getDate() + 1)
            }
        }

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

        if (event.extendedProps.isMaintenance) {
            alert('Maintenance periods cannot be edited')
            return
        }

        const reservation = reservations.value.find((r) => r.id === Number(event.id))

        if (!reservation) return

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

            if (
                props.selectedDeviceData?.maintenance_start &&
                props.selectedDeviceData?.maintenance_end
            ) {
                const maintenanceStart = props.selectedDeviceData.maintenance_start
                const maintenanceEnd = props.selectedDeviceData.maintenance_end

                const startParts = maintenanceStart.split(':').map(Number)
                const endParts = maintenanceEnd.split(':').map(Number)
                const maintenanceStartHour = startParts[0] ?? 0
                const maintenanceStartMinute = startParts[1] ?? 0
                const maintenanceEndHour = endParts[0] ?? 0
                const maintenanceEndMinute = endParts[1] ?? 0

                const currentDate = new Date(startDate)
                currentDate.setHours(0, 0, 0, 0) // Reset to start of day

                const endDateDay = new Date(endDate)
                endDateDay.setHours(23, 59, 59, 999) // Set to end of day

                while (currentDate <= endDateDay) {
                    const dayMaintenanceStart = new Date(currentDate)
                    dayMaintenanceStart.setHours(maintenanceStartHour, maintenanceStartMinute, 0, 0)

                    const dayMaintenanceEnd = new Date(currentDate)
                    dayMaintenanceEnd.setHours(maintenanceEndHour, maintenanceEndMinute, 0, 0)

                    // Calculate the effective reservation period for this specific day
                    const dayStart = new Date(currentDate)
                    dayStart.setHours(0, 0, 0, 0)

                    const dayEnd = new Date(currentDate)
                    dayEnd.setHours(23, 59, 59, 999)

                    // Get the overlap of reservation with this day
                    const effectiveStart = startDate > dayStart ? startDate : dayStart
                    const effectiveEnd = endDate < dayEnd ? endDate : dayEnd

                    // Check if the effective reservation period on this day overlaps with maintenance
                    if (
                        (effectiveStart >= dayMaintenanceStart &&
                            effectiveStart < dayMaintenanceEnd) ||
                        (effectiveEnd > dayMaintenanceStart && effectiveEnd <= dayMaintenanceEnd) ||
                        (effectiveStart <= dayMaintenanceStart && effectiveEnd >= dayMaintenanceEnd)
                    ) {
                        alert(
                            `Reservation conflicts with daily maintenance period (${maintenanceStart} - ${maintenanceEnd})`,
                        )
                        return
                    }

                    currentDate.setDate(currentDate.getDate() + 1)
                }
            }

            const reservationData = {
                device_id: reservationForm.value.deviceId,
                start: startDate.toISOString(),
                end: endDate.toISOString(),
            }

            if (editingReservation.value) {
                await apiClient.patch(
                    `/reservation/${editingReservation.value.id}/`,
                    reservationData,
                )
            } else {
                await apiClient.post('/reservation/', reservationData)
            }

            await fetchReservations()
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
            await apiClient.delete(`/reservation/${editingReservation.value.id}/`)
            await fetchReservations()
            updateCalendarEvents()
            closeModal()
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

            // Check if this is a maintenance event
            if (info.event.extendedProps.isMaintenance) {
                info.el.style.cursor = 'not-allowed'
                info.el.title = 'Maintenance period - cannot be modified'
            } else if (eventEnd && eventEnd < now) {
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
