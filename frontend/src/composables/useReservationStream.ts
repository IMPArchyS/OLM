import { computed, ref } from 'vue';
import { apiClient } from '@/lib/apiClient';
import type { QueueFormData } from '@/types/forms';
import { Command } from '@/types/api';

interface StreamBufferResponse {
    reservation_id: number | null;
    samples: unknown[];
    next_index: number;
    total: number;
}

type OutputRow = Record<string, unknown>;

const POLL_INTERVAL_MS = 750;
const RECONNECT_DELAY_MS = 1000;
const NEXT_INDEX_STORAGE_KEY = 'OLMReservationStreamNextIndex';

const isRecord = (value: unknown): value is OutputRow => {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
};

const isOutputRowArray = (value: unknown): value is OutputRow[] => {
    return Array.isArray(value) && value.every((item) => isRecord(item));
};

const toAuthHeader = (accessToken: string) => {
    return /^Bearer\s+/i.test(accessToken) ? accessToken : `Bearer ${accessToken}`;
};

const parseMessagePayload = (rawMessage: string): OutputRow | null => {
    try {
        const parsed: unknown = JSON.parse(rawMessage);
        return isRecord(parsed) ? parsed : null;
    } catch {
        return null;
    }
};

const extractFinalOutputHistory = (payload: OutputRow): OutputRow[] => {
    const run = payload.run;
    if (isRecord(run) && isOutputRowArray(run.output_history)) {
        return run.output_history;
    }

    const runs = payload.runs;
    if (Array.isArray(runs)) {
        const lastRun = runs.length > 0 ? runs[runs.length - 1] : null;
        if (isRecord(lastRun) && isOutputRowArray(lastRun.output_history)) {
            return lastRun.output_history;
        }
    }

    return [];
};

export function useReservationStream() {
    const websocketRef = ref<WebSocket | null>(null);
    const outputHistory = ref<OutputRow[]>([]);
    const nextIndex = ref(0);
    const statusMessage = ref('');
    const warningMessage = ref('');
    const finalPacket = ref<OutputRow | null>(null);
    const isReservationActive = ref(true);

    const isSocketOnline = ref(false);
    const isActive = ref(false);
    const accessToken = ref<string | null>(null);
    const pendingStartPayload = ref<QueueFormData | null>(null);

    let pollTimer: ReturnType<typeof setInterval> | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let pullInFlight = false;

    const persistNextIndex = (value: number) => {
        sessionStorage.setItem(NEXT_INDEX_STORAGE_KEY, String(value));
    };

    const restoreNextIndex = () => {
        const rawValue = sessionStorage.getItem(NEXT_INDEX_STORAGE_KEY);
        if (!rawValue) {
            return 0;
        }

        const parsed = Number(rawValue);
        if (!Number.isFinite(parsed) || parsed < 0) {
            return 0;
        }

        return Math.floor(parsed);
    };

    const connectionStateText = computed(() => {
        return isSocketOnline.value ? 'WebSocket online.' : 'WebSocket offline. Polling stream buffer.';
    });

    const isReservationEndedReason = (reason: string) => {
        const normalizedReason = reason.toLowerCase();
        return (
            normalizedReason.includes('reservation expired') ||
            normalizedReason.includes('reservation deleted') ||
            normalizedReason.includes('no reservation')
        );
    };

    const markReservationInactive = (reason: string) => {
        isReservationActive.value = false;
        isActive.value = false;
        clearPolling();
        clearReconnectTimer();
        warningMessage.value = reason;
        statusMessage.value = 'Reservation no longer active.';
    };

    function buildWebSocketUrl(token: string) {
        const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin;
        const resolvedApiUrl = new URL(apiBaseUrl, window.location.origin);
        const wsProtocol = resolvedApiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
        const websocketUrl = new URL('/ws/reservation/current', `${wsProtocol}//${resolvedApiUrl.host}`);
        websocketUrl.searchParams.set('access_token', token);
        return websocketUrl.toString();
    }

    const appendRows = (rows: OutputRow[]) => {
        if (rows.length === 0) {
            return;
        }

        outputHistory.value = [...outputHistory.value, ...rows];
    };

    const appendSingleRow = (row: OutputRow) => {
        outputHistory.value = [...outputHistory.value, row];
    };

    const clearPolling = () => {
        if (!pollTimer) {
            return;
        }

        clearInterval(pollTimer);
        pollTimer = null;
    };

    const startPolling = () => {
        if (pollTimer || !isActive.value) {
            return;
        }

        pollTimer = setInterval(() => {
            void pullStreamBuffer();
        }, POLL_INTERVAL_MS);
    };

    const clearReconnectTimer = () => {
        if (!reconnectTimer) {
            return;
        }

        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    };

    const scheduleReconnect = () => {
        if (reconnectTimer || !isActive.value || !accessToken.value) {
            return;
        }

        reconnectTimer = setTimeout(() => {
            reconnectTimer = null;
            if (!isActive.value || !accessToken.value) {
                return;
            }

            connectWebSocket(accessToken.value);
            void pullStreamBuffer();
        }, RECONNECT_DELAY_MS);
    };

    const closeWebSocket = (reason = 'Navigation away from page') => {
        const websocket = websocketRef.value;
        if (!websocket) {
            return;
        }

        if (websocket.readyState === WebSocket.OPEN || websocket.readyState === WebSocket.CONNECTING) {
            websocket.close(1000, reason);
        }

        websocketRef.value = null;
        isSocketOnline.value = false;
    };

    async function pullStreamBuffer() {
        if (!isActive.value || !accessToken.value || pullInFlight) {
            return;
        }

        pullInFlight = true;

        try {
            const response = await apiClient.get<StreamBufferResponse>('/ws/reservation/current/stream-buffer', {
                params: {
                    after_index: nextIndex.value,
                },
                headers: {
                    Authorization: toAuthHeader(accessToken.value),
                },
            });

            const rows = Array.isArray(response.data.samples)
                ? response.data.samples.filter((sample): sample is OutputRow => isRecord(sample))
                : [];

            if (response.data.reservation_id === null) {
                markReservationInactive('Reservation expired or unavailable. Refresh dashboard.');
                closeWebSocket('Reservation no longer active');
                return;
            }

            isReservationActive.value = true;

            appendRows(rows);

            const serverNext = Number.isFinite(response.data.next_index) ? response.data.next_index : nextIndex.value + rows.length;
            nextIndex.value = Math.max(nextIndex.value + rows.length, serverNext);
            persistNextIndex(nextIndex.value);
        } catch (error: unknown) {
            let detail = 'Failed to pull stream buffer.';

            if (typeof error === 'object' && error !== null && 'response' in error) {
                const responseDetail = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail;
                if (typeof responseDetail === 'string' && responseDetail.trim().length > 0) {
                    detail = responseDetail;
                }
            }

            warningMessage.value = detail;
        } finally {
            pullInFlight = false;
        }
    }

    const flushPendingCommandPayload = () => {
        const payload = pendingStartPayload.value;
        const websocket = websocketRef.value;

        if (!payload || !websocket || websocket.readyState !== WebSocket.OPEN) {
            return;
        }

        websocket.send(JSON.stringify(payload));
        pendingStartPayload.value = null;
        statusMessage.value = `Experiment ${String(payload.command ?? '').toUpperCase()} sent.`;
    };

    const handleIncomingPayload = (payload: OutputRow) => {
        if (Object.prototype.hasOwnProperty.call(payload, 'time')) {
            appendSingleRow(payload);
            nextIndex.value += 1;
            persistNextIndex(nextIndex.value);
        }

        if (Object.prototype.hasOwnProperty.call(payload, 'error')) {
            warningMessage.value = String(payload.error ?? 'Experiment stream warning.');
        }

        if (Object.prototype.hasOwnProperty.call(payload, 'run') || Object.prototype.hasOwnProperty.call(payload, 'runs')) {
            finalPacket.value = payload;
            statusMessage.value = 'Final result packet received.';

            const finalHistory = extractFinalOutputHistory(payload);
            if (finalHistory.length > 0) {
                outputHistory.value = finalHistory;
            }
        }
    };

    const connectWebSocket = (token: string) => {
        accessToken.value = token;

        const existing = websocketRef.value;
        if (existing && (existing.readyState === WebSocket.OPEN || existing.readyState === WebSocket.CONNECTING)) {
            return;
        }

        const websocket = new WebSocket(buildWebSocketUrl(token));
        websocketRef.value = websocket;

        websocket.onopen = () => {
            isSocketOnline.value = true;
            warningMessage.value = '';
            statusMessage.value = 'WebSocket connected.';
            clearPolling();
            clearReconnectTimer();
            void pullStreamBuffer();
            flushPendingCommandPayload();
        };

        websocket.onmessage = (event) => {
            const rawMessage = String(event.data ?? '');
            statusMessage.value = rawMessage;

            const payload = parseMessagePayload(rawMessage);
            if (payload) {
                handleIncomingPayload(payload);
            }
        };

        websocket.onerror = () => {
            warningMessage.value = 'WebSocket error. Using pull sync until reconnect.';
        };

        websocket.onclose = (event) => {
            websocketRef.value = null;
            isSocketOnline.value = false;

            if (event.reason && isReservationEndedReason(event.reason)) {
                markReservationInactive(event.reason);
                return;
            }

            if (!isActive.value) {
                return;
            }

            statusMessage.value = connectionStateText.value;
            startPolling();
            scheduleReconnect();
        };
    };

    const activate = (token: string) => {
        isActive.value = true;
        isReservationActive.value = true;
        accessToken.value = token;
        nextIndex.value = restoreNextIndex();
        connectWebSocket(token);
        void pullStreamBuffer();
    };

    const deactivate = () => {
        isActive.value = false;
        pendingStartPayload.value = null;
        clearPolling();
        clearReconnectTimer();
        closeWebSocket();
    };

    const clearGraph = () => {
        outputHistory.value = [];
        finalPacket.value = null;
        nextIndex.value = 0;
        persistNextIndex(nextIndex.value);
    };

    const sendCommand = (payload: QueueFormData): { success: boolean; message?: string } => {
        if (!accessToken.value) {
            return {
                success: false,
                message: 'Authentication required before starting experiment stream.',
            };
        }

        if (!isReservationActive.value) {
            return {
                success: false,
                message: 'Reservation is no longer active. Refresh dashboard.',
            };
        }

        if (payload.command === Command.START) {
            clearGraph();
        }

        warningMessage.value = '';

        pendingStartPayload.value = {
            ...payload,
            input_arguments: { ...payload.input_arguments },
            output_arguments: [...payload.output_arguments],
            setpoint_changes: { ...payload.setpoint_changes },
        };

        const websocket = websocketRef.value;
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            flushPendingCommandPayload();
            return { success: true };
        }

        connectWebSocket(accessToken.value);
        startPolling();

        return { success: true };
    };

    return {
        websocketRef,
        outputHistory,
        nextIndex,
        statusMessage,
        warningMessage,
        finalPacket,
        isSocketOnline,
        isReservationActive,
        activate,
        deactivate,
        pullStreamBuffer,
        sendCommand,
        clearGraph,
    };
}
