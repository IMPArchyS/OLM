import type { Device } from '@/types/api';

const MAINTENANCE_EVENT_RANGE_DAYS = 365;

function parseMaintenanceWindow(maintenanceStart?: string, maintenanceEnd?: string) {
    if (!maintenanceStart || !maintenanceEnd) {
        return null;
    }

    const startParts = maintenanceStart.split(':').map(Number);
    const endParts = maintenanceEnd.split(':').map(Number);

    return {
        startHour: startParts[0] ?? 0,
        startMinute: startParts[1] ?? 0,
        endHour: endParts[0] ?? 0,
        endMinute: endParts[1] ?? 0,
    };
}

function hasTimeRangeOverlap(rangeStart: Date, rangeEnd: Date, blockStart: Date, blockEnd: Date): boolean {
    return (
        (rangeStart >= blockStart && rangeStart < blockEnd) ||
        (rangeEnd > blockStart && rangeEnd <= blockEnd) ||
        (rangeStart <= blockStart && rangeEnd >= blockEnd)
    );
}

export function getMaintenanceConflictMessage(
    startDate: Date,
    endDate: Date,
    maintenanceStart?: string,
    maintenanceEnd?: string,
    messagePrefix = 'Reservation conflicts with daily maintenance period',
): string | null {
    const maintenanceWindow = parseMaintenanceWindow(maintenanceStart, maintenanceEnd);
    if (!maintenanceWindow || startDate > endDate) {
        return null;
    }

    const currentDate = new Date(startDate);
    currentDate.setHours(0, 0, 0, 0);

    const endDateDay = new Date(endDate);
    endDateDay.setHours(23, 59, 59, 999);

    while (currentDate <= endDateDay) {
        const dayMaintenanceStart = new Date(currentDate);
        dayMaintenanceStart.setHours(maintenanceWindow.startHour, maintenanceWindow.startMinute, 0, 0);

        const dayMaintenanceEnd = new Date(currentDate);
        dayMaintenanceEnd.setHours(maintenanceWindow.endHour, maintenanceWindow.endMinute, 0, 0);

        const dayStart = new Date(currentDate);
        dayStart.setHours(0, 0, 0, 0);

        const dayEnd = new Date(currentDate);
        dayEnd.setHours(23, 59, 59, 999);

        const effectiveStart = startDate > dayStart ? startDate : dayStart;
        const effectiveEnd = endDate < dayEnd ? endDate : dayEnd;

        if (hasTimeRangeOverlap(effectiveStart, effectiveEnd, dayMaintenanceStart, dayMaintenanceEnd)) {
            return `${messagePrefix} (${maintenanceStart} - ${maintenanceEnd})`;
        }

        currentDate.setDate(currentDate.getDate() + 1);
    }

    return null;
}

export function buildMaintenanceEvents(device?: Device | null) {
    if (!device?.maintenance_start || !device?.maintenance_end) {
        return [];
    }

    const maintenanceWindow = parseMaintenanceWindow(device.maintenance_start, device.maintenance_end);
    if (!maintenanceWindow) {
        return [];
    }

    const today = new Date();

    return Array.from({ length: MAINTENANCE_EVENT_RANGE_DAYS * 2 }, (_, index) => {
        const offset = index - MAINTENANCE_EVENT_RANGE_DAYS;
        const eventDate = new Date(today);
        eventDate.setDate(today.getDate() + offset);

        const startDateTime = new Date(eventDate);
        startDateTime.setHours(maintenanceWindow.startHour, maintenanceWindow.startMinute, 0, 0);

        const endDateTime = new Date(eventDate);
        endDateTime.setHours(maintenanceWindow.endHour, maintenanceWindow.endMinute, 0, 0);

        return {
            id: `maintenance-${offset}`,
            title: 'Maintenance',
            start: startDateTime.toISOString(),
            end: endDateTime.toISOString(),
            backgroundColor: '#ef4444',
            borderColor: '#dc2626',
            extendedProps: {
                deviceId: device.id,
                isMaintenance: true,
            },
        };
    });
}

export function formatDateTimeLocal(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}
