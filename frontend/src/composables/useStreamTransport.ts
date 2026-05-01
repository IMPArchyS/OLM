import { ref } from 'vue';
import type { Ref } from 'vue';
import { apiClient } from '@/lib/apiClient';

export type OutputRow = Record<string, unknown>;

interface StreamBufferResponse {
    reservation_id: number | null;
    samples: unknown[];
    next_index: number;
    total: number;
}

export interface StreamTransportCallbacks {
    onMessage: (payload: OutputRow) => void;
    onConnected: () => void;
    onSamplesReceived: (rows: OutputRow[], serverNextIndex: number | null) => void;
    onReservationExpired: (reason: string) => void;
    onWarning: (message: string) => void;
    onStatus: (message: string) => void;
}

const POLL_INTERVAL_MS = 750;
const RECONNECT_DELAY_MS = 1000;

export const isRecord = (value: unknown): value is OutputRow =>
    typeof value === 'object' && value !== null && !Array.isArray(value);

const toAuthHeader = (token: string) =>
    /^Bearer\s+/i.test(token) ? token : `Bearer ${token}`;

const parseMessagePayload = (raw: string): OutputRow | null => {
    try {
        const parsed: unknown = JSON.parse(raw);
        return isRecord(parsed) ? parsed : null;
    } catch {
        return null;
    }
};

const isReservationEndedReason = (reason: string): boolean => {
    const r = reason.toLowerCase();
    return r.includes('reservation expired') || r.includes('reservation deleted') || r.includes('no reservation');
};

function buildWebSocketUrl(token: string): string {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin;
    const resolved = new URL(apiBaseUrl, window.location.origin);
    const wsProtocol = resolved.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = new URL('/ws/reservation/current', `${wsProtocol}//${resolved.host}`);
    url.searchParams.set('access_token', token);
    return url.toString();
}

export function useStreamTransport(
    isActive: Ref<boolean>,
    accessToken: Ref<string | null>,
    nextIndex: Ref<number>,
    callbacks: StreamTransportCallbacks,
) {
    const websocketRef = ref<WebSocket | null>(null);
    const isSocketOnline = ref(false);

    let pollTimer: ReturnType<typeof setInterval> | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let pullInFlight = false;

    const clearPolling = () => {
        if (!pollTimer) return;
        clearInterval(pollTimer);
        pollTimer = null;
    };

    const startPolling = () => {
        if (pollTimer || !isActive.value) return;
        pollTimer = setInterval(() => { void pullStreamBuffer(); }, POLL_INTERVAL_MS);
    };

    const clearReconnectTimer = () => {
        if (!reconnectTimer) return;
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    };

    const scheduleReconnect = () => {
        if (reconnectTimer || !isActive.value || !accessToken.value) return;
        reconnectTimer = setTimeout(() => {
            reconnectTimer = null;
            if (!isActive.value || !accessToken.value) return;
            connect(accessToken.value);
            void pullStreamBuffer();
        }, RECONNECT_DELAY_MS);
    };

    const disconnect = (reason = 'Navigation away from page') => {
        const ws = websocketRef.value;
        if (!ws) return;
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
            ws.close(1000, reason);
        }
        websocketRef.value = null;
        isSocketOnline.value = false;
    };

    const sendMessage = (data: string): boolean => {
        const ws = websocketRef.value;
        if (!ws || ws.readyState !== WebSocket.OPEN) return false;
        ws.send(data);
        return true;
    };

    const isConnected = (): boolean => {
        const ws = websocketRef.value;
        return ws !== null && ws.readyState === WebSocket.OPEN;
    };

    async function pullStreamBuffer() {
        if (!isActive.value || !accessToken.value || pullInFlight) return;
        pullInFlight = true;

        try {
            const response = await apiClient.get<StreamBufferResponse>('/ws/reservation/current/stream-buffer', {
                params: { after_index: nextIndex.value },
                headers: { Authorization: toAuthHeader(accessToken.value) },
            });

            const rows = Array.isArray(response.data.samples)
                ? response.data.samples.filter((s): s is OutputRow => isRecord(s))
                : [];

            if (response.data.reservation_id === null) {
                clearPolling();
                clearReconnectTimer();
                callbacks.onReservationExpired('Reservation expired or unavailable. Refresh dashboard.');
                disconnect('Reservation no longer active');
                return;
            }

            const rawNext = response.data.next_index;
            if (!Number.isFinite(rawNext)) {
                callbacks.onWarning('Stream index fallback: server returned invalid next_index.');
            }
            callbacks.onSamplesReceived(rows, Number.isFinite(rawNext) ? rawNext : null);
        } catch (error: unknown) {
            let detail = 'Failed to pull stream buffer.';
            if (typeof error === 'object' && error !== null && 'response' in error) {
                const d = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail;
                if (typeof d === 'string' && d.trim().length > 0) detail = d;
            }
            callbacks.onWarning(detail);
        } finally {
            pullInFlight = false;
        }
    }

    const connect = (token: string) => {
        const existing = websocketRef.value;
        if (existing && (existing.readyState === WebSocket.OPEN || existing.readyState === WebSocket.CONNECTING)) {
            return;
        }

        const ws = new WebSocket(buildWebSocketUrl(token));
        websocketRef.value = ws;

        ws.onopen = () => {
            isSocketOnline.value = true;
            callbacks.onWarning('');
            callbacks.onStatus('WebSocket connected.');
            clearPolling();
            clearReconnectTimer();
            void pullStreamBuffer();
            callbacks.onConnected();
        };

        ws.onmessage = (event) => {
            const raw = String(event.data ?? '');
            const payload = parseMessagePayload(raw);
            if (payload) {
                callbacks.onMessage(payload);
                return;
            }
            callbacks.onStatus(raw);
        };

        ws.onerror = () => {
            callbacks.onWarning('WebSocket error. Using pull sync until reconnect.');
        };

        ws.onclose = (event) => {
            websocketRef.value = null;
            isSocketOnline.value = false;

            if (event.reason && isReservationEndedReason(event.reason)) {
                clearPolling();
                clearReconnectTimer();
                callbacks.onReservationExpired(event.reason);
                return;
            }

            if (!isActive.value) return;

            callbacks.onStatus('WebSocket offline. Polling stream buffer.');
            startPolling();
            scheduleReconnect();
        };
    };

    return {
        websocketRef,
        isSocketOnline,
        connect,
        disconnect,
        pullStreamBuffer,
        startPolling,
        clearPolling,
        clearReconnectTimer,
        sendMessage,
        isConnected,
    };
}
