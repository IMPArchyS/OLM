import { ref } from 'vue';
import { apiClient } from '../lib/apiClient';
import axios from 'axios';
import type { Server } from '@/types/api';

interface GrantToken {
    device_name: string;
    grant_token: string;
    expires_at: string;
}

export function useWebRtc() {
    const grantToken = ref<GrantToken | null>(null);
    const activeServerId = ref<number | null>(null);
    const activeDeviceName = ref<string | null>(null);
    const remoteStream = ref<MediaStream | null>(null);
    const peerConnection = ref<RTCPeerConnection | null>(null);
    const activeServiceBaseUrl = ref<string | null>(null);
    const loading = ref(false);
    const error = ref<string | null>(null);
    const SERVICE_WEBRTC_PREFIX = '/api/server/devices';

    function cleanupLocalStream(pc: RTCPeerConnection | null = peerConnection.value): void {
        if (pc) {
            pc.close();
            if (peerConnection.value === pc) {
                peerConnection.value = null;
            }
        }

        if (remoteStream.value) {
            remoteStream.value.getTracks().forEach((track) => track.stop());
            remoteStream.value = null;
        }
    }

    function encodeDeviceName(deviceName: string): string {
        return encodeURIComponent(deviceName);
    }

    function getAuthHeaderCandidates(token: string): string[] {
        const trimmed = token.trim();
        if (!trimmed) {
            return [];
        }

        if (/^Bearer\s+/i.test(trimmed)) {
            return [trimmed, trimmed.replace(/^Bearer\s+/i, '')];
        }

        return [trimmed, `Bearer ${trimmed}`];
    }

    async function postToServiceWithAuthFallback<T = unknown>(url: string, token: string, data: unknown = null): Promise<T> {
        const candidates = getAuthHeaderCandidates(token);
        let lastError: any = null;

        for (const authValue of candidates) {
            try {
                const response = await axios.post<T>(url, data, {
                    headers: {
                        Authorization: authValue,
                        'Content-Type': 'application/json',
                    },
                    withCredentials: true,
                });
                return response.data;
            } catch (e: any) {
                lastError = e;
                if (e?.response?.status !== 401) {
                    break;
                }
            }
        }

        throw lastError;
    }

    function buildServiceBaseUrl(server: Server): string {
        const rawDomain = server.api_domain.trim();
        const hasProtocol = /^https?:\/\//i.test(rawDomain);
        const apiBaseProtocol = (() => {
            try {
                return new URL(import.meta.env.VITE_API_BASE_URL ?? window.location.origin, window.location.origin).protocol;
            } catch {
                return 'http:';
            }
        })();
        const defaultProtocol = apiBaseProtocol || 'http:';
        const normalized = hasProtocol ? rawDomain : `${defaultProtocol}//${rawDomain}`;

        const parsedUrl = new URL(normalized);
        parsedUrl.port = String(server.port);
        parsedUrl.pathname = '';
        parsedUrl.search = '';
        parsedUrl.hash = '';
        return parsedUrl.origin;
    }

    async function resolveServiceBaseUrl(serverId: number): Promise<string> {
        if (activeServerId.value === serverId && activeServiceBaseUrl.value) {
            return activeServiceBaseUrl.value;
        }

        const response = await apiClient.get<Server>(`/server/${serverId}`);
        const serviceBaseUrl = buildServiceBaseUrl(response.data);

        activeServerId.value = serverId;
        activeServiceBaseUrl.value = serviceBaseUrl;

        return serviceBaseUrl;
    }

    async function requestGrant(serverId: number, deviceName: string, ttlSeconds = 300): Promise<GrantToken | null> {
        loading.value = true;
        error.value = null;

        try {
            const encodedDeviceName = encodeDeviceName(deviceName);
            const response = await apiClient.post<GrantToken>(`/webrtc/${serverId}/${encodedDeviceName}/grants`);

            grantToken.value = response.data;
            activeServerId.value = serverId;
            activeDeviceName.value = deviceName;

            try {
                await resolveServiceBaseUrl(serverId);
            } catch {
                // Service URL is also resolved lazily in start/stop and can fail independently.
            }

            return response.data;
        } catch (e: any) {
            grantToken.value = null;
            error.value = e.response?.data?.message || e.message || 'Failed to request WebRTC grant';
            return null;
        } finally {
            loading.value = false;
        }
    }

    async function refreshGrant(
        serverId: number | null = activeServerId.value,
        deviceName: string | null = activeDeviceName.value,
        token: string | null = grantToken.value?.grant_token ?? null,
    ): Promise<GrantToken | null> {
        if (serverId === null || !deviceName || !token) {
            error.value = 'Cannot refresh WebRTC grant without server, device, and grant token';
            return null;
        }

        loading.value = true;
        error.value = null;

        try {
            const encodedDeviceName = encodeDeviceName(deviceName);
            const refreshBody = { grant_token: token };

            let response;
            try {
                response = await apiClient.post<GrantToken>(`/webrtc/${serverId}/${encodedDeviceName}/grants/refresh`, refreshBody);
            } catch (e: any) {
                if (e?.response?.status !== 404) {
                    throw e;
                }

                response = await apiClient.post<GrantToken>(`/webrtc/${serverId}/${encodedDeviceName}/grants/refresh/`, refreshBody);
            }

            grantToken.value = response.data;
            activeServerId.value = serverId;
            activeDeviceName.value = deviceName;
            return response.data;
        } catch (e: any) {
            error.value =
                e.response?.data?.message ||
                e.message ||
                'Failed to refresh WebRTC grant. If this persists, verify backend refresh route/service forwarding.';
            return null;
        } finally {
            loading.value = false;
        }
    }

    async function startVideoStream(
        deviceName: string,
        token: GrantToken,
        serverId: number | null = activeServerId.value,
    ): Promise<RTCPeerConnection> {
        if (serverId === null) {
            error.value = 'Missing server_id for starting video stream';
            throw new Error(error.value);
        }

        loading.value = true;
        error.value = null;

        cleanupLocalStream();
        grantToken.value = token;
        activeServerId.value = serverId;
        activeDeviceName.value = deviceName;

        const pc = new RTCPeerConnection();
        peerConnection.value = pc;

        pc.ontrack = (event) => {
            remoteStream.value = event.streams[0] ?? null;
        };

        try {
            const serviceBaseUrl = await resolveServiceBaseUrl(serverId);
            const encodedDeviceName = encodeDeviceName(deviceName);
            const offer = await pc.createOffer({ offerToReceiveVideo: true });
            await pc.setLocalDescription(offer);

            const answer = await postToServiceWithAuthFallback<RTCSessionDescriptionInit>(
                `${serviceBaseUrl}${SERVICE_WEBRTC_PREFIX}/${encodedDeviceName}/webrtc/offer`,
                token.grant_token,
                { sdp: offer.sdp, type: offer.type },
            );

            await pc.setRemoteDescription(new RTCSessionDescription(answer));
            return pc;
        } catch (e: any) {
            error.value = e.response?.data?.message || e.message || 'Failed to start video stream';

            pc.close();
            if (peerConnection.value === pc) {
                peerConnection.value = null;
            }
            activeDeviceName.value = null;

            throw e;
        } finally {
            loading.value = false;
        }
    }

    async function stopVideoStream(
        serverId: number | null = activeServerId.value,
        deviceName: string | null = activeDeviceName.value,
        token: GrantToken | null = grantToken.value,
        pc: RTCPeerConnection | null = peerConnection.value,
    ): Promise<void> {
        if (serverId !== null && deviceName && token) {
            try {
                const serviceBaseUrl = await resolveServiceBaseUrl(serverId);
                const encodedDeviceName = encodeDeviceName(deviceName);

                await postToServiceWithAuthFallback(`${serviceBaseUrl}${SERVICE_WEBRTC_PREFIX}/${encodedDeviceName}/webrtc/stop`, token.grant_token);
            } catch (e: any) {
                error.value = e.response?.data?.message || e.message || 'Failed to stop video stream';
            }
        }

        cleanupLocalStream(pc);

        activeDeviceName.value = null;
        activeServiceBaseUrl.value = null;
    }

    return {
        grantToken,
        activeServerId,
        activeDeviceName,
        activeServiceBaseUrl,
        remoteStream,
        loading,
        error,
        requestGrant,
        refreshGrant,
        startVideoStream,
        stopVideoStream,
    };
}
