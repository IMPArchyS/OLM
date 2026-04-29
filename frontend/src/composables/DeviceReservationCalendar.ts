import { computed, ref, watch } from 'vue';
import type { CalendarOptions, DateSelectArg, EventClickArg } from '@fullcalendar/core';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import listPlugin from '@fullcalendar/list';
import skLocale from '@fullcalendar/core/locales/sk';
import timeGridPlugin from '@fullcalendar/timegrid';
import { useI18n } from 'vue-i18n';
import type { Device, Reservation } from '@/types/api';
import type { ReservationForm } from '@/types/forms';
import { useToastStore } from '@/stores/toast';
import { useReservations } from '@/composables/useReservations';
import { buildMaintenanceEvents, formatDateTimeLocal, getMaintenanceConflictMessage } from '@/composables/reservationCalendarUtils';

interface Props {
    selectedDeviceId?: number | null;
    selectedDeviceData?: Device | null;
}

export function useDeviceReservationCalendar(props: Props) {
    const toast = useToastStore();
    const { locale, t } = useI18n();
    const {
        reservations,
        loading,
        fetchReservations,
        createReservation,
        updateReservation,
        deleteReservation: removeReservation,
    } = useReservations();
    const isModalOpen = ref(false);
    const editingReservation = ref<Reservation | null>(null);
    const fullCalendar = ref();
    const reservationForm = ref<ReservationForm>({ device_id: 0, start: '', end: '' });

    async function refreshReservations() {
        if (!props.selectedDeviceId) {
            reservations.value = [];
            return { success: true };
        }
        const result = await fetchReservations(props.selectedDeviceId);
        if (!result.success) toast.error(result.message || 'Failed to fetch reservations');
        return result;
    }

    watch(
        () => props.selectedDeviceId,
        async (newDeviceId) => {
            if (newDeviceId) await refreshReservations();
            else reservations.value = [];
        },
        { immediate: true },
    );

    const calendarEvents = computed(() => {
        const reservationEvents = reservations.value.map((r) => ({
            id: String(r.id),
            title: r.username || 'Reserved',
            start: r.start,
            end: r.end,
            backgroundColor: undefined,
            extendedProps: { deviceId: r.device_id, isMaintenance: false },
        }));
        return [...reservationEvents, ...buildMaintenanceEvents(props.selectedDeviceData)];
    });

    function checkMaintenanceConflict(startDate: Date, endDate: Date, messagePrefix: string) {
        const message = getMaintenanceConflictMessage(
            startDate,
            endDate,
            props.selectedDeviceData?.maintenance_start,
            props.selectedDeviceData?.maintenance_end,
            messagePrefix,
        );
        if (message) {
            toast.error(message);
            return true;
        }
        return false;
    }

    const MAX_DURATION_MS = 30 * 60 * 1000;

    function resolveAllDaySlot(date: Date): { start: Date; end: Date } {
        const now = new Date();
        const isToday = date.toDateString() === now.toDateString();
        const start = isToday
            ? new Date(Math.ceil(now.getTime() / MAX_DURATION_MS) * MAX_DURATION_MS)
            : new Date(new Date(date).setHours(12, 0, 0, 0));
        return { start, end: new Date(start.getTime() + MAX_DURATION_MS) };
    }

    function handleDateSelect(selectInfo: DateSelectArg) {
        selectInfo.view.calendar.unselect();
        if (!props.selectedDeviceId) return;

        let start = selectInfo.start;
        let end = selectInfo.end;

        if (selectInfo.allDay) {
            const slot = resolveAllDaySlot(start);
            start = slot.start;
            end = slot.end;
        }

        if (checkMaintenanceConflict(start, end, 'Cannot create reservation during maintenance period')) return;
        reservationForm.value = {
            device_id: props.selectedDeviceId,
            start: formatDateTimeLocal(start),
            end: formatDateTimeLocal(end),
        };
        editingReservation.value = null;
        isModalOpen.value = true;
    }

    function handleEventClick(clickInfo: EventClickArg) {
        const event = clickInfo.event;
        if (event.extendedProps.isMaintenance) {
            if (clickInfo.view.type === 'dayGridMonth' && props.selectedDeviceId && event.start) {
                const slot = resolveAllDaySlot(event.start);
                if (checkMaintenanceConflict(slot.start, slot.end, 'Cannot create reservation during maintenance period')) return;
                reservationForm.value = {
                    device_id: props.selectedDeviceId,
                    start: formatDateTimeLocal(slot.start),
                    end: formatDateTimeLocal(slot.end),
                };
                editingReservation.value = null;
                isModalOpen.value = true;
                return;
            }
            toast.warning('Maintenance periods cannot be edited');
            return;
        }
        const reservation = reservations.value.find((r) => r.id === Number(event.id));
        if (!reservation) return;
        if (new Date(reservation.end) < new Date()) {
            toast.warning('Cannot edit past reservations');
            return;
        }
        editingReservation.value = reservation;
        reservationForm.value = {
            device_id: reservation.device_id,
            start: formatDateTimeLocal(new Date(reservation.start)),
            end: formatDateTimeLocal(new Date(reservation.end)),
        };
        isModalOpen.value = true;
    }

    async function saveReservation() {
        const startDate = new Date(reservationForm.value.start);
        const endDate = new Date(reservationForm.value.end);
        if (startDate < new Date() || endDate < new Date()) {
            toast.error('Cannot create reservation in the past');
            return;
        }
        if (endDate.getTime() - startDate.getTime() > MAX_DURATION_MS) {
            toast.error('Reservation cannot be longer than 30 minutes');
            return;
        }
        if (checkMaintenanceConflict(startDate, endDate, 'Reservation conflicts with daily maintenance period')) return;
        const reservationData = { device_id: reservationForm.value.device_id, start: startDate.toISOString(), end: endDate.toISOString() };
        const result = editingReservation.value
            ? await updateReservation(editingReservation.value.id, reservationData)
            : await createReservation(reservationData);
        if (!result.success) {
            toast.error(result.message || 'Failed to save reservation');
            return;
        }
        const refreshResult = await refreshReservations();
        if (!refreshResult.success) return;
        updateCalendarEvents();
        closeModal();
    }

    async function deleteReservation() {
        if (!editingReservation.value) return;
        const result = await removeReservation(editingReservation.value.id);
        if (!result.success) {
            toast.error(result.message || 'Failed to delete reservation');
            return;
        }
        const refreshResult = await refreshReservations();
        if (!refreshResult.success) return;
        updateCalendarEvents();
        closeModal();
    }

    function updateCalendarEvents() {
        if (!fullCalendar.value) return;
        const calendarApi = fullCalendar.value.getApi();
        calendarApi.removeAllEvents();
        calendarApi.addEventSource(calendarEvents.value);
    }

    function closeModal() {
        isModalOpen.value = false;
        editingReservation.value = null;
    }

    const calendarOptions = computed<CalendarOptions>(() => ({
        plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin, listPlugin],
        locale: locale.value === 'sk' ? skLocale : 'en',
        firstDay: 1,
        initialView: 'timeGridWeek',
        timeZone: 'local',
        headerToolbar: { left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek,timeGridDay' },
        buttonText: {
            today: t('calendar.today'),
            month: t('calendar.month'),
            week: t('calendar.week'),
            day: t('calendar.day'),
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
        selectAllow: (selectInfo) => selectInfo.allDay || selectInfo.end.getTime() - selectInfo.start.getTime() <= MAX_DURATION_MS,
        eventClick: handleEventClick,
        eventAllow: (_dropInfo, draggedEvent) => (draggedEvent?.start ? draggedEvent.start >= new Date() : true),
        eventDidMount: (info) => {
            const eventEnd = info.event.end || info.event.start;
            if (info.event.extendedProps.isMaintenance) {
                info.el.style.cursor = 'not-allowed';
            } else if (eventEnd && eventEnd < new Date()) {
                info.el.style.opacity = '0.6';
                info.el.style.cursor = 'not-allowed';
            }
        },
        height: '100%',
        themeSystem: 'standard',
        selectConstraint: { start: new Date().toISOString() },
        stickyHeaderDates: true,
        stickyFooterScrollbar: true,
    }));

    return {
        reservations,
        isModalOpen,
        editingReservation,
        fullCalendar,
        reservationForm,
        calendarOptions,
        calendarEvents,
        loading,
        fetchReservations: refreshReservations,
        handleDateSelect,
        handleEventClick,
        saveReservation,
        deleteReservation,
        updateCalendarEvents,
        closeModal,
    };
}
