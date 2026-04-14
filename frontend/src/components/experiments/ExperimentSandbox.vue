<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { Command, type Reservation } from '@/types/api';
import ExperimentSelector from './ExperimentSelector.vue';
import type { QueueFormData } from '@/types/forms';
import { useExperiments } from '@/composables/useExperiments';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import { useToastStore } from '@/stores/toast';
import CameraView from '@/components/dashboard/CameraView.vue';
import SimpleOutputChart from './SimpleOutputChart.vue';

interface Props {
    reservation: Reservation;
    cameraDeviceName?: string;
    cameraServerId?: number;
    resolvingCameraTarget?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
    cameraDeviceName: '',
    cameraServerId: 0,
    resolvingCameraTarget: false,
});

const { t } = useI18n();
const authStore = useAuthStore();
const toast = useToastStore();
const { experimentsByDevice, loading, fetchExperimentsByDevice } = useExperiments();

const websocketRef = ref<WebSocket | null>(null);
const websocketMessage = ref('');
const outputHistory = ref<Record<string, unknown>[]>([]);

type SandboxPanelId = 'control' | 'chart' | 'camera' | 'animation';

const defaultPanelOrder: SandboxPanelId[] = ['control', 'chart', 'camera', 'animation'];
const visiblePanelOrder = ref<SandboxPanelId[]>([...defaultPanelOrder]);

const panelTitles = computed<Record<SandboxPanelId, string>>(() => {
    return {
        control: 'Experiment control',
        chart: 'Live output',
        camera: 'Camera stream',
        animation: 'Experiment animation',
    };
});

const isPanelVisible = (panelId: SandboxPanelId) => {
    return visiblePanelOrder.value.includes(panelId);
};

const togglePanelVisibility = (panelId: SandboxPanelId, visible: boolean) => {
    if (visible) {
        if (!visiblePanelOrder.value.includes(panelId)) {
            visiblePanelOrder.value = [...visiblePanelOrder.value, panelId];
        }
        return;
    }

    visiblePanelOrder.value = visiblePanelOrder.value.filter((item) => item !== panelId);
};

const resetPanelOrder = () => {
    visiblePanelOrder.value = [...defaultPanelOrder];
};

const canRunExperiment = computed(() => {
    return experimentsByDevice.value.length > 0 && formData.value.id !== null;
});

const isOutputRow = (value: unknown): value is Record<string, unknown> => {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
};

const isOutputRowArray = (value: unknown): value is Record<string, unknown>[] => {
    return Array.isArray(value) && value.every((item) => isOutputRow(item));
};

const parseOutputHistory = (rawMessage: string): Record<string, unknown>[] | null => {
    try {
        const payload: unknown = JSON.parse(rawMessage);

        if (isOutputRowArray(payload)) {
            return payload;
        }

        if (isOutputRow(payload) && isOutputRowArray(payload.output_history)) {
            return payload.output_history;
        }

        // TODO: Confirm websocket payload contract for incremental output updates, then support append mode.
        return null;
    } catch {
        return null;
    }
};

function buildWebSocketUrl(accessToken: string) {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin;
    const resolvedApiUrl = new URL(apiBaseUrl, window.location.origin);
    const wsProtocol = resolvedApiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    const websocketUrl = new URL('/ws/reservation/current', `${wsProtocol}//${resolvedApiUrl.host}`);
    websocketUrl.searchParams.set('access_token', accessToken);
    return websocketUrl.toString();
}

function closeWebSocket() {
    const websocket = websocketRef.value;
    if (!websocket) return;

    if (websocket.readyState === WebSocket.OPEN || websocket.readyState === WebSocket.CONNECTING) {
        websocket.close(1000, 'Navigation away from page');
    }

    websocketRef.value = null;
}

onBeforeUnmount(() => {
    closeWebSocket();
});

onBeforeRouteLeave(() => {
    closeWebSocket();
});

function runExperiment() {
    const selectedExperiment = experimentsByDevice.value.find((exp) => exp.id === formData.value.id);
    formData.value.output_arguments = selectedExperiment?.output_arguments ?? [];

    console.log(JSON.stringify(formData.value, null, 2));

    websocketMessage.value = '';
    outputHistory.value = [];
    closeWebSocket();

    const accessToken = authStore.accessToken || localStorage.getItem('OLMAccessToken');
    if (!accessToken) {
        websocketMessage.value = 'Authentication required before starting the experiment.';
        toast.error('Authentication required before starting the experiment.');
        return;
    }

    const websocket = new WebSocket(buildWebSocketUrl(accessToken));
    websocketRef.value = websocket;

    websocket.onopen = () => {
        console.log('WebSocket Created');
        websocket.send(JSON.stringify(formData.value));
    };

    websocket.onmessage = (event) => {
        const rawMessage = String(event.data);
        websocketMessage.value = rawMessage;

        const parsedOutputHistory = parseOutputHistory(rawMessage);
        if (parsedOutputHistory) {
            outputHistory.value = parsedOutputHistory;
        }

        console.log('WebSocket response:', event.data);
    };

    websocket.onerror = (error) => {
        websocketMessage.value = 'WebSocket error. Please try running the experiment again.';
        console.error('WebSocket error:', error);
    };

    websocket.onclose = () => {
        websocketRef.value = null;
        if (!websocketMessage.value) {
            websocketMessage.value = 'WebSocket closed.';
        } else {
            websocketMessage.value = `${websocketMessage.value} (connection closed)`;
        }
        console.log('WebSocket closed');
    };
}

const formData = ref<QueueFormData>({
    user_id: authStore.user?.id ?? null,
    id: null,
    command: Command.START,
    input_arguments: {},
    output_arguments: [],
    setpoint_changes: {},
    schema_id: null,
    device_id: null,
    software_name: null,
    simulation_time: 0,
    sample_rate: 0,
});

onMounted(async () => {
    const result = await fetchExperimentsByDevice(props.reservation.device_id);
    if (!result.success) {
        toast.error(result.message || 'Failed');
    }
});

const handleFormDataUpdate = (data: typeof formData.value) => {
    formData.value = data;
};
</script>

<template>
    <v-card class="mt-4 sandbox-card">
        <v-card-title class="text-h6">{{ t('dashboard.ongoing_experiment') }}</v-card-title>

        <v-card-text class="pt-2">
            <v-card variant="outlined" class="sandbox-filter-card">
                <v-card-title class="text-subtitle-2">Visible sections</v-card-title>
                <v-card-text class="pb-2">
                    <div class="sandbox-filter-grid">
                        <v-checkbox
                            v-for="panelId in defaultPanelOrder"
                            :key="`toggle-${panelId}`"
                            :model-value="isPanelVisible(panelId)"
                            :label="panelTitles[panelId]"
                            hide-details
                            density="compact"
                            @update:model-value="(value) => togglePanelVisibility(panelId, Boolean(value))"
                        />
                    </div>

                    <div class="sandbox-filter-actions">
                        <v-btn size="small" variant="tonal" prepend-icon="mdi-backup-restore" @click="resetPanelOrder">Reset order</v-btn>
                    </div>
                </v-card-text>
            </v-card>

            <v-alert v-if="visiblePanelOrder.length === 0" type="info" variant="tonal" class="mt-3">
                No section selected. Enable at least one section above.
            </v-alert>

            <v-row dense class="align-stretch">
                <v-col v-for="panelId in visiblePanelOrder" :key="panelId" cols="12" lg="6" class="d-flex">
                    <v-card variant="outlined" class="sandbox-section-card d-flex flex-column w-100">
                        <v-card-title class="text-subtitle-1">{{ panelTitles[panelId] }}</v-card-title>
                        <v-card-text class="sandbox-section-body d-flex flex-column flex-grow-1">
                            <div v-if="panelId === 'control'" class="sandbox-panel-content">
                                <ExperimentSelector
                                    fixed-command=""
                                    :loading="loading"
                                    :experiments="experimentsByDevice"
                                    :selected-device-id="props.reservation.device_id"
                                    compact
                                    @update:formData="handleFormDataUpdate"
                                />

                                <v-btn color="info" prepend-icon="mdi-play" @click="runExperiment" :disabled="!canRunExperiment">
                                    {{ t('dashboard.run_experiment') }}
                                </v-btn>
                            </div>

                            <div v-else-if="panelId === 'chart'" class="sandbox-chart-panel">
                                <SimpleOutputChart :output-history="outputHistory" title="Live output" :height="240" fill-container class="h-100" />

                                <v-alert v-if="websocketMessage" type="info" variant="tonal" class="mt-3">
                                    <div class="text-caption">{{ websocketMessage }}</div>
                                </v-alert>
                            </div>

                            <div v-else-if="panelId === 'camera'" class="sandbox-camera-panel">
                                <v-alert v-if="props.resolvingCameraTarget" type="info" variant="tonal">Resolving camera target...</v-alert>
                                <v-alert v-else-if="!props.cameraDeviceName || !props.cameraServerId" type="warning" variant="tonal">
                                    Unable to resolve server/device for camera stream from this reservation.
                                </v-alert>
                                <CameraView v-else :device_name="props.cameraDeviceName" :server_id="props.cameraServerId" compact class="h-100" />
                            </div>

                            <div v-else class="animation-placeholder-wrapper">
                                <!-- TODO: Replace placeholder with animation component once API and asset contract are finalized. -->
                                <div class="animation-placeholder">
                                    <v-icon icon="mdi-chart-timeline-variant" size="42" class="mb-2" />
                                    <div class="text-body-2">Animation placeholder</div>
                                </div>
                            </div>
                        </v-card-text>
                    </v-card>
                </v-col>
            </v-row>
        </v-card-text>
    </v-card>
</template>

<style scoped>
.sandbox-card {
    overflow: visible;
}

.sandbox-filter-card {
    margin-bottom: 12px;
}

.sandbox-filter-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 4px 12px;
}

.sandbox-filter-actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 8px;
}

.sandbox-section-card {
    height: 100%;
}

.sandbox-section-body {
    min-height: 0;
}

.sandbox-panel-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
    flex: 1 1 auto;
}

.sandbox-chart-panel,
.sandbox-camera-panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
    flex: 1 1 auto;
}

.animation-placeholder {
    min-height: 200px;
    width: 100%;
    flex: 1 1 auto;
    border: 1px dashed rgba(var(--v-theme-on-surface), 0.2);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    color: rgba(var(--v-theme-on-surface), 0.7);
}

.sandbox-camera-panel :deep(.camera-view),
.sandbox-chart-panel :deep(.simple-output-chart) {
    flex: 1 1 auto;
}
</style>
