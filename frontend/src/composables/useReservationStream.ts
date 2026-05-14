import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import type { ExperimentFormData } from '@/types/forms';
import { Command } from '@/types/api';
import { useToastStore } from '@/stores/toast';
import { useStreamTransport, isRecord } from './useStreamTransport';
import type { OutputRow } from './useStreamTransport';

const isOutputRowArray = (value: unknown): value is OutputRow[] =>
    Array.isArray(value) && value.every((item) => isRecord(item));

const extractFinalOutputHistory = (payload: OutputRow): OutputRow[] => {
    const run = payload.run;
    if (isRecord(run) && isOutputRowArray(run.output_history)) return run.output_history;

    const runs = payload.runs;
    if (Array.isArray(runs)) {
        const lastRun = runs.length > 0 ? runs[runs.length - 1] : null;
        if (isRecord(lastRun) && isOutputRowArray(lastRun.output_history)) return lastRun.output_history;
    }
    return [];
};

const parseNumericTime = (payload: OutputRow): number | null => {
    const raw = payload.time;
    if (typeof raw === 'number' && Number.isFinite(raw)) return raw;
    if (typeof raw === 'string') {
        const parsed = Number(raw);
        if (Number.isFinite(parsed)) return parsed;
    }
    return null;
};

export function useReservationStream() {
    const toast = useToastStore();
    const { t } = useI18n();

    const outputHistory = ref<OutputRow[]>([]);
    const nextIndex = ref(0);
    const statusMessage = ref('');
    const warningMessage = ref('');
    const finalPacket = ref<OutputRow | null>(null);
    const isReservationActive = ref(false);
    const isActive = ref(false);
    const accessToken = ref<string | null>(null);
    const pendingStartPayload = ref<ExperimentFormData | null>(null);
    const awaitingStartAcceptance = ref(false);
    const baselineTimeBeforeStart = ref<number | null>(null);

    const clearGraph = () => {
        outputHistory.value = [];
        finalPacket.value = null;
        nextIndex.value = 0;
    };

    const appendRows = (rows: OutputRow[]) => {
        if (rows.length > 0) outputHistory.value.push(...rows);
    };

    const latestNumericTimeFromHistory = (): number | null => {
        for (let i = outputHistory.value.length - 1; i >= 0; i -= 1) {
            const row = outputHistory.value[i];
            if (!row) continue;
            const t = parseNumericTime(row);
            if (t !== null) return t;
        }
        return null;
    };

    const markReservationInactive = (reason: string) => {
        isReservationActive.value = false;
        isActive.value = false;
        warningMessage.value = reason;
        statusMessage.value = 'Reservation no longer active.';
        toast.warning(t('dashboard.toast_reservation_expired'));
    };

    const markUpstreamUnavailable = (reason: string) => {
        isActive.value = false;
        warningMessage.value = reason;
        statusMessage.value = 'Device server unavailable.';
        awaitingStartAcceptance.value = false;
        baselineTimeBeforeStart.value = null;
        pendingStartPayload.value = null;
        toast.error(t('dashboard.toast_device_server_unavailable'));
    };

    const transport = useStreamTransport(isActive, accessToken, nextIndex, {
        onMessage: (payload) => handleIncomingPayload(payload),
        onConnected: () => flushPendingCommandPayload(),
        onSamplesReceived: (rows, serverNextIndex) => {
            isReservationActive.value = true;
            appendRows(rows);
            const fallback = nextIndex.value + rows.length;
            nextIndex.value = Math.max(0, Math.floor(serverNextIndex ?? fallback));
        },
        onReservationExpired: (reason) => markReservationInactive(reason),
        onUpstreamUnavailable: (reason) => markUpstreamUnavailable(reason),
        onWarning: (msg) => { warningMessage.value = msg; },
        onStatus: (msg) => { statusMessage.value = msg; },
    });

    function flushPendingCommandPayload() {
        const payload = pendingStartPayload.value;
        if (!payload) return;
        if (!transport.sendMessage(JSON.stringify(payload))) return;
        pendingStartPayload.value = null;
        const commandLabel = String(payload.command ?? '').toUpperCase();
        statusMessage.value = `Experiment ${commandLabel} sent.`;
        if (payload.command === Command.CHANGE) toast.info(t('dashboard.toast_experiment_changed'));
        else if (payload.command === Command.STOP) toast.info(t('dashboard.toast_experiment_stop_requested'));
    }

    function handleIncomingPayload(payload: OutputRow) {
        if (Object.prototype.hasOwnProperty.call(payload, 'time')) {
            const numericTime = parseNumericTime(payload);
            if (awaitingStartAcceptance.value) {
                const baseline = baselineTimeBeforeStart.value;
                if (numericTime !== null && (baseline === null || numericTime < baseline)) {
                    clearGraph();
                    awaitingStartAcceptance.value = false;
                    baselineTimeBeforeStart.value = null;
                    toast.success(t('dashboard.toast_experiment_started'));
                }
            }
            appendRows([payload]);
            nextIndex.value += 1;
        }

        if (Object.prototype.hasOwnProperty.call(payload, 'error')) {
            const msg = String(payload.error ?? 'Experiment stream warning.');
            warningMessage.value = msg;
            toast.error(msg);
            statusMessage.value = 'Command rejected by experiment service.';
            awaitingStartAcceptance.value = false;
            baselineTimeBeforeStart.value = null;
        }

        if (Object.prototype.hasOwnProperty.call(payload, 'run') || Object.prototype.hasOwnProperty.call(payload, 'runs')) {
            finalPacket.value = payload;
            statusMessage.value = 'Final result packet received.';
            toast.success(t('dashboard.toast_experiment_finished'));
            const finalHistory = extractFinalOutputHistory(payload);
            if (finalHistory.length > 0) outputHistory.value = finalHistory;
            awaitingStartAcceptance.value = false;
            baselineTimeBeforeStart.value = null;
        }
    }

    const activate = (token: string) => {
        isActive.value = true;
        isReservationActive.value = true;
        accessToken.value = token;
        clearGraph();
        transport.connect(token);
        void transport.pullStreamBuffer();
    };

    const deactivate = () => {
        isActive.value = false;
        pendingStartPayload.value = null;
        awaitingStartAcceptance.value = false;
        baselineTimeBeforeStart.value = null;
        transport.clearPolling();
        transport.clearReconnectTimer();
        transport.disconnect();
    };

    const sendCommand = (payload: ExperimentFormData): { success: boolean; message?: string } => {
        if (!accessToken.value) {
            return { success: false, message: 'Authentication required before starting experiment stream.' };
        }
        if (!isReservationActive.value) {
            return { success: false, message: 'Reservation is no longer active. Refresh dashboard.' };
        }
        if (payload.command === Command.START) {
            awaitingStartAcceptance.value = true;
            baselineTimeBeforeStart.value = latestNumericTimeFromHistory();
        }
        warningMessage.value = '';
        pendingStartPayload.value = {
            ...payload,
            input_arguments: { ...payload.input_arguments },
            output_arguments: [...payload.output_arguments],
            setpoint_changes: { ...payload.setpoint_changes },
        };
        if (transport.isConnected()) {
            flushPendingCommandPayload();
            return { success: true };
        }
        transport.connect(accessToken.value);
        transport.startPolling();
        return { success: true };
    };

    return {
        websocketRef: transport.websocketRef,
        outputHistory,
        nextIndex,
        statusMessage,
        warningMessage,
        finalPacket,
        isSocketOnline: transport.isSocketOnline,
        isReservationActive,
        activate,
        deactivate,
        pullStreamBuffer: transport.pullStreamBuffer,
        sendCommand,
        clearGraph,
    };
}
