import type { ExperimentHistoryItem, ExperimentLog, FinishReason } from '@/types/api';

export const finishReasonColorMap: Record<FinishReason, string> = {
    'n/a': 'secondary',
    user_stop: 'secondary',
    simulation_time_reached: 'success',
    device_timeout: 'warning',
    exception_error: 'error',
};

export const finishReasonI18nKey: Record<FinishReason, string> = {
    'n/a': 'reports.finishReasons.na',
    user_stop: 'reports.finishReasons.userStop',
    simulation_time_reached: 'reports.finishReasons.simulationTimeReached',
    device_timeout: 'reports.finishReasons.deviceTimeout',
    exception_error: 'reports.finishReasons.exceptionError',
};

export const formatDateTime = (value?: string | null): string => {
    if (!value) return 'N/A';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
};

export const getFinishReasonColor = (reason: FinishReason): string => {
    return finishReasonColorMap[reason] ?? 'secondary';
};

export const extractTimeSeries = (log: ExperimentLog): number[] => {
    const outputHistory = log.run?.output_history ?? [];
    return outputHistory
        .map((row) => {
            const rawTime = row.time;
            if (typeof rawTime === 'number' && Number.isFinite(rawTime)) return rawTime;
            if (typeof rawTime === 'string') {
                const parsed = Number(rawTime);
                if (Number.isFinite(parsed)) return parsed;
            }
            return null;
        })
        .filter((value): value is number => value !== null);
};

export const estimateSimulationTime = (log: ExperimentLog): number | null => {
    const times = extractTimeSeries(log);
    if (times.length === 0) return null;
    const minTime = Math.min(...times);
    const maxTime = Math.max(...times);
    const duration = maxTime - minTime + 1;
    return Number((duration > 0 ? duration : maxTime).toFixed(3));
};

export const estimateSampleInterval = (log: ExperimentLog): number | null => {
    const times = extractTimeSeries(log);
    if (times.length < 2) return null;
    const deltas: number[] = [];
    for (let index = 1; index < times.length; index += 1) {
        const previous = times[index - 1];
        const current = times[index];
        if (previous === undefined || current === undefined) continue;
        const delta = current - previous;
        if (delta > 0 && Number.isFinite(delta)) deltas.push(delta);
    }
    if (deltas.length === 0) return null;
    const averageDelta = deltas.reduce((sum, value) => sum + value, 0) / deltas.length;
    return Number(averageDelta.toFixed(3));
};

export const formatSimTime = (log: ExperimentLog): string => {
    const value = estimateSimulationTime(log);
    return value !== null ? `${value} s` : 'N/A';
};

export const formatSampleInterval = (log: ExperimentLog): string => {
    const value = estimateSampleInterval(log);
    return value !== null ? `${value} s` : 'N/A';
};

export const formatArgValue = (rawValue: unknown): string => {
    if (rawValue === null || rawValue === undefined) return 'N/A';
    if (typeof rawValue === 'object' && !Array.isArray(rawValue)) {
        const valueField = (rawValue as { value?: unknown }).value;
        if (valueField !== undefined) return String(valueField);
        return JSON.stringify(rawValue);
    }
    return String(rawValue);
};

export const formatArgUnit = (rawValue: unknown): string => {
    if (typeof rawValue === 'object' && rawValue !== null && !Array.isArray(rawValue)) {
        const unitField = (rawValue as { unit?: unknown }).unit;
        if (typeof unitField === 'string' && unitField.trim().length > 0) return unitField;
    }
    return '-';
};

export const getInputArgumentRows = (entry: ExperimentHistoryItem): Array<{ key: string; value: string; unit: string }> => {
    return Object.entries(entry.input_args ?? {}).map(([key, rawValue]) => ({
        key,
        value: formatArgValue(rawValue),
        unit: formatArgUnit(rawValue),
    }));
};

export const getLogTitle = (log: ExperimentLog, t: (key: string) => string): string => {
    const server = log.server_name ?? String(log.server_id);
    const device = log.device_name ?? String(log.device_id);
    const parts = [server, device];
    if (log.software_name) parts.push(log.software_name);
    return `${t('reports.logPrefix')} - ${parts.join(' | ')}`;
};

export const formatFinishReason = (reason: FinishReason, t: (key: string) => string): string => {
    return t(finishReasonI18nKey[reason] ?? 'reports.finishReasons.na');
};

export const getRunStatus = (log: ExperimentLog, t: (key: string) => string): { text: string; color: string } => {
    if (!log.started_at) return { text: t('reports.status.notStarted'), color: 'secondary' };
    if (!log.finished_at || log.finish_reason === 'n/a') return { text: t('reports.status.pending'), color: 'info' };
    if (log.finish_reason === 'device_timeout') return { text: t('reports.status.timedOut'), color: 'warning' };
    if (log.finish_reason === 'user_stop') return { text: t('reports.status.stopped'), color: 'secondary' };
    if (log.finish_reason === 'exception_error') return { text: t('reports.status.error'), color: 'error' };
    if (log.finish_reason === 'simulation_time_reached' && log.finished_at) return { text: t('reports.status.finished'), color: 'success' };
    return { text: t('reports.status.pending'), color: 'info' };
};
