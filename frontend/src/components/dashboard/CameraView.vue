<script lang="ts" setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { useWebRtc } from '@/composables/useWebRtc';
import { useToastStore } from '@/stores/toast';

const props = defineProps<{
    device_name: string;
    server_id: number;
}>();

const videoRef = ref<HTMLVideoElement | null>(null);
const isStreaming = ref(false);
const GRANT_REFRESH_INTERVAL_MS = 1 * 60 * 1000;
let grantRefreshIntervalId: number | null = null;

const { remoteStream, loading, error, requestGrant, refreshGrant, startVideoStream, stopVideoStream } = useWebRtc();
const toast = useToastStore();

const canStart = computed(() => {
    return !loading.value && !isStreaming.value && props.server_id > 0 && props.device_name.length > 0;
});

const canStop = computed(() => {
    return !loading.value && isStreaming.value;
});

watch(remoteStream, (stream) => {
    if (videoRef.value) {
        videoRef.value.srcObject = stream;
    }

    if (!stream) {
        isStreaming.value = false;
    }
});

watch(error, (message) => {
    if (message) {
        toast.error(message);
    }
});

watch(
    () => [props.device_name, props.server_id],
    () => {
        if (isStreaming.value) {
            void handleStop();
        }
    },
);

async function handleStart(): Promise<void> {
    if (!props.device_name || props.server_id <= 0) {
        toast.error('Missing device_name or server_id for camera stream');
        return;
    }

    const token = await requestGrant(props.server_id, props.device_name);
    if (!token) {
        return;
    }

    try {
        await startVideoStream(props.device_name, token, props.server_id);
        isStreaming.value = true;
        startGrantRefresh();
    } catch {
        isStreaming.value = false;
        stopGrantRefresh();
    }
}

async function handleRefreshGrant(): Promise<void> {
    if (!isStreaming.value) {
        return;
    }

    await refreshGrant(props.server_id, props.device_name);
}

async function handleStop(): Promise<void> {
    stopGrantRefresh();
    await stopVideoStream(props.server_id, props.device_name);
    isStreaming.value = false;
}

function stopGrantRefresh(): void {
    if (grantRefreshIntervalId !== null) {
        clearInterval(grantRefreshIntervalId);
        grantRefreshIntervalId = null;
    }
}

function startGrantRefresh(): void {
    stopGrantRefresh();
    grantRefreshIntervalId = window.setInterval(() => {
        void handleRefreshGrant();
    }, GRANT_REFRESH_INTERVAL_MS);
}

onBeforeUnmount(() => {
    stopGrantRefresh();
    void handleStop();
});
</script>

<template>
    <v-card class="mt-4">
        <v-card-title>Camera Stream</v-card-title>
        <v-card-text>
            <div class="mb-3 text-body-2">
                <strong>Device:</strong> {{ props.device_name || 'N/A' }}
                <span class="mx-2">|</span>
                <strong>Server ID:</strong> {{ props.server_id || 'N/A' }}
            </div>

            <video ref="videoRef" autoplay playsinline muted class="camera-video"></video>

            <div class="d-flex flex-wrap gap-2 mt-3">
                <v-btn color="primary" :loading="loading" :disabled="!canStart" @click="handleStart">Start Stream</v-btn>
                <v-btn color="error" :loading="loading" :disabled="!canStop" @click="handleStop">Stop Stream</v-btn>
            </div>

            <v-alert v-if="error" type="error" variant="tonal" class="mt-3">
                {{ error }}
            </v-alert>
        </v-card-text>
    </v-card>
</template>

<style scoped>
.camera-video {
    width: 100%;
    min-height: 240px;
    border-radius: 8px;
    background: #000;
    object-fit: contain;
}
</style>
