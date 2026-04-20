<script setup lang="ts">
import { useResizeObserver } from '@vueuse/core';
import { GridItem, GridLayout, type Layout } from 'grid-layout-plus';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { Command, type DeviceType, type Reservation } from '@/types/api';
import ExperimentSelector from './ExperimentSelector.vue';
import type { QueueFormData } from '@/types/forms';
import { useExperiments } from '@/composables/useExperiments';
import { useReservationStream } from '@/composables/useReservationStream';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import { useToastStore } from '@/stores/toast';
import CameraView from '@/components/dashboard/CameraView.vue';
import SimpleOutputChart from './SimpleOutputChart.vue';
import DeviceAnimationPanel from './DeviceAnimationPanel.vue';

interface Props {
    reservation: Reservation;
    deviceType?: DeviceType | null;
    cameraDeviceName?: string;
    cameraServerId?: number;
    resolvingCameraTarget?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
    deviceType: null,
    cameraDeviceName: '',
    cameraServerId: 0,
    resolvingCameraTarget: false,
});

const { t } = useI18n();
const authStore = useAuthStore();
const toast = useToastStore();
const { experimentsByDevice, loading, fetchExperimentsByDevice } = useExperiments();
const { outputHistory, statusMessage, warningMessage, activate, deactivate, sendCommand, isSocketOnline, isReservationActive } =
    useReservationStream();

type SandboxPanelId = 'control' | 'chart' | 'camera' | 'animation';

const STORAGE_LAYOUT_KEY = 'olm:sandbox:grid-layout:v1';
const STORAGE_VISIBILITY_KEY = 'olm:sandbox:grid-visibility:v1';
const panelIds: SandboxPanelId[] = ['control', 'chart', 'camera', 'animation'];

const defaultPanelMeta: Record<
    SandboxPanelId,
    {
        title: string;
        icon: string;
        minW: number;
        minH: number;
        defaultW: number;
        defaultH: number;
        defaultX: number;
        defaultY: number;
    }
> = {
    control: {
        title: 'Experiment control',
        icon: 'mdi-tune-vertical-variant',
        minW: 4,
        minH: 12,
        defaultW: 6,
        defaultH: 15,
        defaultX: 0,
        defaultY: 0,
    },
    chart: {
        title: 'Live output',
        icon: 'mdi-chart-line',
        minW: 4,
        minH: 10,
        defaultW: 6,
        defaultH: 10,
        defaultX: 6,
        defaultY: 0,
    },
    camera: {
        title: 'Camera stream',
        icon: 'mdi-video-wireless',
        minW: 4,
        minH: 10,
        defaultW: 6,
        defaultH: 10,
        defaultX: 0,
        defaultY: 15,
    },
    animation: {
        title: 'Experiment animation',
        icon: 'mdi-chart-timeline-variant',
        minW: 4,
        minH: 10,
        defaultW: 6,
        defaultH: 10,
        defaultX: 6,
        defaultY: 10,
    },
};

const makeDefaultLayout = (): Layout => {
    return panelIds.map((panelId) => {
        const meta = defaultPanelMeta[panelId];
        return {
            i: panelId,
            x: meta.defaultX,
            y: meta.defaultY,
            w: meta.defaultW,
            h: meta.defaultH,
            minW: meta.minW,
            minH: meta.minH,
        };
    });
};

const readStoredLayout = (): Layout => {
    const fallback = makeDefaultLayout();
    const raw = localStorage.getItem(STORAGE_LAYOUT_KEY);
    if (!raw) {
        return fallback;
    }

    try {
        const parsed = JSON.parse(raw) as Layout;
        if (!Array.isArray(parsed)) {
            return fallback;
        }

        return panelIds.map((panelId) => {
            const meta = defaultPanelMeta[panelId];
            const item = parsed.find((entry) => String(entry.i) === panelId);
            if (!item) {
                return {
                    i: panelId,
                    x: meta.defaultX,
                    y: meta.defaultY,
                    w: meta.defaultW,
                    h: meta.defaultH,
                    minW: meta.minW,
                    minH: meta.minH,
                };
            }

            return {
                i: panelId,
                x: Number.isFinite(item.x) ? item.x : meta.defaultX,
                y: Number.isFinite(item.y) ? item.y : meta.defaultY,
                w: Math.max(meta.minW, Number.isFinite(item.w) ? item.w : meta.defaultW),
                h: Math.max(meta.minH, Number.isFinite(item.h) ? item.h : meta.defaultH),
                minW: meta.minW,
                minH: meta.minH,
            };
        });
    } catch {
        return fallback;
    }
};

const readPanelVisibility = (): Record<SandboxPanelId, boolean> => {
    const fallback: Record<SandboxPanelId, boolean> = {
        control: true,
        chart: true,
        camera: true,
        animation: true,
    };

    const raw = localStorage.getItem(STORAGE_VISIBILITY_KEY);
    if (!raw) {
        return fallback;
    }

    try {
        const parsed = JSON.parse(raw) as Partial<Record<SandboxPanelId, unknown>>;
        return {
            control: parsed.control === undefined ? true : Boolean(parsed.control),
            chart: parsed.chart === undefined ? true : Boolean(parsed.chart),
            camera: parsed.camera === undefined ? true : Boolean(parsed.camera),
            animation: parsed.animation === undefined ? true : Boolean(parsed.animation),
        };
    } catch {
        return fallback;
    }
};

const panelLayout = ref<Layout>(readStoredLayout());
const panelVisibility = ref<Record<SandboxPanelId, boolean>>(readPanelVisibility());
const gridContainerRef = ref<HTMLElement | null>(null);
const gridRowHeight = ref(20);

const panelTitles = computed<Record<SandboxPanelId, string>>(() => {
    return {
        control: defaultPanelMeta.control.title,
        chart: defaultPanelMeta.chart.title,
        camera: defaultPanelMeta.camera.title,
        animation: defaultPanelMeta.animation.title,
    };
});

const panelIcons = computed<Record<SandboxPanelId, string>>(() => {
    return {
        control: defaultPanelMeta.control.icon,
        chart: defaultPanelMeta.chart.icon,
        camera: defaultPanelMeta.camera.icon,
        animation: defaultPanelMeta.animation.icon,
    };
});

const itemPanelId = (itemId: number | string): SandboxPanelId => {
    return String(itemId) as SandboxPanelId;
};

const isPanelVisible = (panelId: SandboxPanelId): boolean => {
    return panelVisibility.value[panelId];
};

const setPanelVisibility = (panelId: SandboxPanelId, visible: boolean) => {
    panelVisibility.value = {
        ...panelVisibility.value,
        [panelId]: visible,
    };
};

const mergeLayoutWithMeta = (layout: Layout): Layout => {
    return panelIds.map((panelId) => {
        const meta = defaultPanelMeta[panelId];
        const item = layout.find((entry) => String(entry.i) === panelId);

        return {
            i: panelId,
            x: item?.x ?? meta.defaultX,
            y: item?.y ?? meta.defaultY,
            w: Math.max(meta.minW, item?.w ?? meta.defaultW),
            h: Math.max(meta.minH, item?.h ?? meta.defaultH),
            minW: meta.minW,
            minH: meta.minH,
        };
    });
};

const persistLayoutState = () => {
    localStorage.setItem(STORAGE_LAYOUT_KEY, JSON.stringify(panelLayout.value));
    localStorage.setItem(STORAGE_VISIBILITY_KEY, JSON.stringify(panelVisibility.value));
};

const visiblePanelLayout = computed<Layout>(() => {
    return panelLayout.value.filter((entry) => panelVisibility.value[itemPanelId(entry.i)]);
});

const resetLayout = () => {
    panelVisibility.value = {
        control: true,
        chart: true,
        camera: true,
        animation: true,
    };
    panelLayout.value = makeDefaultLayout();
};

const handleLayoutUpdate = (layout: Layout) => {
    const layoutById = new Map(layout.map((entry) => [String(entry.i), entry]));
    const merged = panelLayout.value.map((entry) => layoutById.get(String(entry.i)) ?? entry);
    panelLayout.value = mergeLayoutWithMeta(merged);
};

watch(panelLayout, persistLayoutState, { deep: true });
watch(panelVisibility, persistLayoutState, { deep: true });

panelLayout.value = mergeLayoutWithMeta(panelLayout.value);

useResizeObserver(gridContainerRef, (entries) => {
    const entry = entries[0];
    if (!entry) {
        return;
    }

    const width = entry.contentRect.width;
    if (width < 700) {
        gridRowHeight.value = 16;
        return;
    }

    if (width < 1100) {
        gridRowHeight.value = 18;
        return;
    }

    gridRowHeight.value = 20;
});

const canRunExperiment = computed(() => {
    return experimentsByDevice.value.length > 0 && formData.value.id !== null;
});

const deviceVisualConfig = computed(() => {
    return props.deviceType?.visual_config ?? null;
});

onBeforeRouteLeave(() => {
    deactivate();
});

onBeforeUnmount(() => {
    deactivate();
});

function runExperiment() {
    const selectedExperiment = experimentsByDevice.value.find((exp) => exp.id === formData.value.id);
    formData.value.output_arguments = selectedExperiment?.output_arguments ?? [];

    console.log(JSON.stringify(formData.value, null, 2));

    const accessToken = authStore.accessToken || localStorage.getItem('OLMAccessToken');
    if (!accessToken) {
        toast.error('Authentication required before starting the experiment.');
        return;
    }

    const sendResult = sendCommand(formData.value);
    if (!sendResult.success) {
        toast.error(sendResult.message ?? 'Failed to send command.');
    }
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

    const accessToken = authStore.accessToken || localStorage.getItem('OLMAccessToken');
    if (!accessToken) {
        return;
    }

    activate(accessToken);
});

const handleFormDataUpdate = (data: typeof formData.value) => {
    formData.value = data;
};
</script>

<template>
    <v-card class="mt-4 sandbox-card">
        <v-card-title class="sandbox-toolbar">
            <span class="text-h6">{{ t('dashboard.ongoing_experiment') }}</span>
            <div class="sandbox-toolbar-controls sandbox-no-drag">
                <div class="sandbox-toolbar-toggles">
                    <v-checkbox
                        v-for="panelId in panelIds"
                        :key="`toggle-${panelId}`"
                        :model-value="isPanelVisible(panelId)"
                        density="compact"
                        hide-details
                        color="primary"
                        class="sandbox-panel-toggle"
                        @update:model-value="(value) => setPanelVisibility(panelId, Boolean(value))"
                    >
                        <template #label>
                            <div class="d-flex align-center ga-1">
                                <v-icon :icon="panelIcons[panelId]" size="14" />
                                <span class="text-caption">{{ panelTitles[panelId] }}</span>
                            </div>
                        </template>
                    </v-checkbox>
                </div>

                <v-btn size="x-small" variant="tonal" prepend-icon="mdi-backup-restore" class="sandbox-no-drag" @click="resetLayout">
                    Reset layout
                </v-btn>
            </div>
        </v-card-title>

        <v-card-text class="pt-2">
            <v-alert v-if="!isReservationActive" type="warning" variant="tonal" density="compact" class="sandbox-reservation-alert mb-2">
                Reservation has ended. Dashboard updates automatically when next reservation becomes active.
            </v-alert>

            <template v-else>
                <div class="sandbox-debug-row" aria-live="polite">
                    <v-alert type="info" variant="tonal" density="compact" class="sandbox-debug-alert mb-0">
                        <div class="text-caption">{{ isSocketOnline ? 'WebSocket online.' : 'WebSocket offline. Pulling stream buffer.' }}</div>
                    </v-alert>

                    <v-alert v-if="statusMessage" type="info" variant="tonal" density="compact" class="sandbox-debug-alert mb-0">
                        <div class="text-caption">{{ statusMessage }}</div>
                    </v-alert>

                    <v-alert v-if="warningMessage" type="warning" variant="tonal" density="compact" class="sandbox-debug-alert mb-0">
                        <div class="text-caption">{{ warningMessage }}</div>
                    </v-alert>
                </div>

                <v-alert v-if="visiblePanelLayout.length === 0" density="compact" variant="tonal" type="info" class="mb-2">
                    No panels enabled. Use panel controls to toggle panels on.
                </v-alert>

                <div ref="gridContainerRef" class="sandbox-grid-host">
                    <GridLayout
                        :layout="visiblePanelLayout"
                        :col-num="12"
                        :row-height="gridRowHeight"
                        :margin="[12, 12]"
                        :is-draggable="true"
                        :is-resizable="true"
                        :is-bounded="true"
                        :use-css-transforms="true"
                        :vertical-compact="false"
                        class="sandbox-grid-layout"
                        @update:layout="handleLayoutUpdate"
                    >
                        <GridItem
                            v-for="item in visiblePanelLayout"
                            :key="String(item.i)"
                            :x="item.x"
                            :y="item.y"
                            :w="item.w"
                            :h="item.h"
                            :i="item.i"
                            :min-w="item.minW ?? 4"
                            :min-h="item.minH ?? defaultPanelMeta[itemPanelId(item.i)].minH"
                            :is-resizable="true"
                            drag-ignore-from=".sandbox-no-drag, button, input, textarea, select, .v-field, .v-btn, .v-input, .v-selection-control, .sandbox-animation-panel, .sandbox-animation-panel *"
                            class="sandbox-grid-item"
                        >
                            <v-card variant="outlined" class="sandbox-section-card d-flex flex-column w-100">
                                <div class="sandbox-panel-handle sandbox-section-header">
                                    <div class="sandbox-section-title">
                                        <v-icon :icon="panelIcons[itemPanelId(item.i)]" size="18" />
                                        <span class="text-subtitle-1">{{ panelTitles[itemPanelId(item.i)] }}</span>
                                    </div>
                                </div>

                                <v-card-text class="sandbox-section-body d-flex flex-column grow">
                                    <div v-if="itemPanelId(item.i) === 'control'" class="sandbox-panel-content">
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

                                    <div v-else-if="itemPanelId(item.i) === 'chart'" class="sandbox-chart-panel">
                                        <SimpleOutputChart
                                            :output-history="outputHistory"
                                            title="Live output"
                                            :height="240"
                                            fill-container
                                            class="h-100"
                                        />
                                    </div>

                                    <div v-else-if="itemPanelId(item.i) === 'camera'" class="sandbox-camera-panel">
                                        <v-alert v-if="props.resolvingCameraTarget" type="info" variant="tonal" density="compact">
                                            Resolving camera target...
                                        </v-alert>
                                        <v-alert
                                            v-else-if="!props.cameraDeviceName || !props.cameraServerId"
                                            type="warning"
                                            variant="tonal"
                                            density="compact"
                                        >
                                            Unable to resolve server/device for camera stream from this reservation.
                                        </v-alert>
                                        <CameraView
                                            v-else
                                            :device_name="props.cameraDeviceName"
                                            :server_id="props.cameraServerId"
                                            compact
                                            class="h-100"
                                        />
                                    </div>

                                    <div v-else class="sandbox-animation-panel">
                                        <DeviceAnimationPanel :visual-config="deviceVisualConfig" :output-history="outputHistory" class="h-100" />
                                    </div>
                                </v-card-text>
                            </v-card>
                        </GridItem>
                    </GridLayout>
                </div>
            </template>
        </v-card-text>
    </v-card>
</template>

<style scoped>
.sandbox-card {
    overflow: visible;
}

.sandbox-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px 12px;
}

.sandbox-toolbar-controls {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex: 1 1 460px;
    gap: 6px 12px;
    flex-wrap: wrap;
}

.sandbox-toolbar-toggles {
    display: flex;
    align-items: center;
    gap: 2px 10px;
    flex-wrap: wrap;
}

.sandbox-panel-toggle {
    margin-inline: -4px;
    margin-block: 0;
}

.sandbox-panel-toggle :deep(.v-selection-control) {
    min-height: 22px;
}

.sandbox-debug-alert {
    flex: 1 1 240px;
    min-width: 0;
    overflow-wrap: anywhere;
    word-break: break-word;
}

.sandbox-debug-alert :deep(.v-alert__content) {
    font-size: 12px;
    line-height: 1.25;
}

.sandbox-reservation-alert :deep(.v-alert__content) {
    font-size: 13px;
}

.sandbox-debug-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 8px;
}

.sandbox-grid-host {
    width: 100%;
}

.sandbox-grid-layout {
    min-height: 560px;
    border-radius: 12px;
    background: rgba(var(--v-theme-surface-variant), 0.2);
    padding: 6px;
}

.sandbox-grid-item {
    min-height: 0;
}

.sandbox-section-card {
    height: 100%;
    overflow: hidden;
}

.sandbox-section-header {
    display: flex;
    align-items: center;
    padding: 10px 12px;
    border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
    cursor: move;
}

.sandbox-section-title {
    display: flex;
    align-items: center;
    gap: 8px;
}

.sandbox-section-body {
    min-height: 0;
    overflow: auto;
}

.sandbox-panel-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
    flex: 1 1 auto;
}

.sandbox-chart-panel,
.sandbox-camera-panel,
.sandbox-animation-panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
    flex: 1 1 auto;
    min-height: 0;
}

.sandbox-camera-panel :deep(.camera-view),
.sandbox-chart-panel :deep(.simple-output-chart),
.sandbox-animation-panel :deep(.device-animation-panel) {
    flex: 1 1 auto;
}

.sandbox-grid-layout :deep(.vgl-item.vgl-item--placeholder) {
    border-radius: 10px;
    background: rgba(var(--v-theme-primary), 0.14);
}

@media (max-width: 960px) {
    .sandbox-toolbar-controls {
        justify-content: flex-start;
        flex-basis: 100%;
    }

    .sandbox-debug-alert {
        flex-basis: 100%;
    }

    .sandbox-grid-layout {
        min-height: 640px;
    }
}
</style>
