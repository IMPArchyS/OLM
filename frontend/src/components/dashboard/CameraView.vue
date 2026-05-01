<script lang="ts" setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { useWebRtc } from '@/composables/useWebRtc';
import { useToastStore } from '@/stores/toast';
import { useI18n } from 'vue-i18n';

interface Props {
    device_name: string;
    server_id: number;
    compact?: boolean;
    hideTitle?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
    compact: false,
    hideTitle: false,
});

const videoRef = ref<HTMLVideoElement | null>(null);
const isStreaming = ref(false);
const GRANT_REFRESH_INTERVAL_MS = 1 * 60 * 1000;
let grantRefreshIntervalId: number | null = null;

const { remoteStream, loading, error, requestGrant, refreshGrant, startVideoStream, stopVideoStream } = useWebRtc();
const toast = useToastStore();
const { t } = useI18n();

const canToggle = computed(() => !loading.value && props.server_id > 0 && props.device_name.length > 0);

const toggleState = computed(() =>
    isStreaming.value
        ? { label: t('camera.stop'), color: 'error', icon: 'mdi-video-off' }
        : { label: t('camera.start'), color: 'primary', icon: 'mdi-video' },
);

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
        toast.error(t('camera.missingProps'));
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

async function handleToggleStream(): Promise<void> {
    if (isStreaming.value) {
        await handleStop();
        return;
    }

    await handleStart();
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
    <v-card :class="['camera-view', { 'camera-view--compact': props.compact }]" :variant="props.compact ? 'flat' : undefined">
        <v-card-title v-if="!props.hideTitle">{{ t('camera.title') }}</v-card-title>
        <v-card-text class="camera-content">
            <div class="camera-stage">
                <video ref="videoRef" autoplay playsinline muted class="camera-video"></video>
            </div>

            <div class="camera-controls">
                <v-btn
                    :color="toggleState.color"
                    :size="props.compact ? 'small' : 'default'"
                    :prepend-icon="toggleState.icon"
                    :loading="loading"
                    :disabled="!canToggle"
                    block
                    @click="handleToggleStream"
                >
                    {{ toggleState.label }}
                </v-btn>
            </div>
        </v-card-text>
    </v-card>
</template>

<style scoped>
.camera-view {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.camera-content {
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    min-height: 0;
}

.camera-stage {
    flex: 1 1 auto;
    min-height: 0;
}

.camera-controls {
    margin-top: 8px;
    flex-shrink: 0;
}

.camera-video {
    width: 100%;
    height: 100%;
    min-height: 0;
    border-radius: 8px;
    background: #000;
    object-fit: contain;
}
</style>
