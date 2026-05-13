import { apiClient } from '@/lib/apiClient';

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

export async function fetchMaintenanceEvents(deviceId: number, from: Date, to: Date, title?: string): Promise<any[]> {
    try {
        const fromStr = from.toISOString().split('T')[0];
        const toStr = to.toISOString().split('T')[0];
        const response = await apiClient.get(`/device/${deviceId}/maintenance-events`, {
            params: { from: fromStr, to: toStr },
        });
        if (title) {
            return response.data.map((event: any) => ({ ...event, title }));
        }
        return response.data;
    } catch {
        return [];
    }
}

export function formatDateTimeLocal(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}
