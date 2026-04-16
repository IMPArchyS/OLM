<script setup lang="ts">
import { useResizeObserver } from '@vueuse/core';
import { GridItem, GridLayout, type Layout } from 'grid-layout-plus';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { Command, type Reservation } from '@/types/api';
import ExperimentSelector from './ExperimentSelector.vue';
import type { QueueFormData } from '@/types/forms';
import { useExperiments } from '@/composables/useExperiments';
import { useReservationStream } from '@/composables/useReservationStream';
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
const { outputHistory, statusMessage, warningMessage, activate, deactivate, sendCommand, isSocketOnline, isReservationActive } =
    useReservationStream();

type SandboxPanelId = 'control' | 'chart' | 'camera' | 'animation';

const STORAGE_LAYOUT_KEY = 'olm:sandbox:grid-layout:v1';
const STORAGE_COLLAPSE_KEY = 'olm:sandbox:grid-collapse:v1';
const COLLAPSED_PANEL_HEIGHT = 3;
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

const defaultExpandedHeights: Record<SandboxPanelId, number> = {
    control: defaultPanelMeta.control.defaultH,
    chart: defaultPanelMeta.chart.defaultH,
    camera: defaultPanelMeta.camera.defaultH,
    animation: defaultPanelMeta.animation.defaultH,
};

const expandedHeights = ref<Record<SandboxPanelId, number>>({ ...defaultExpandedHeights });

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
                h: Math.max(COLLAPSED_PANEL_HEIGHT, Number.isFinite(item.h) ? item.h : meta.defaultH),
                minW: meta.minW,
                minH: meta.minH,
            };
        });
    } catch {
        return fallback;
    }
};

const readCollapsedPanels = (): Record<SandboxPanelId, boolean> => {
    const fallback: Record<SandboxPanelId, boolean> = {
        control: false,
        chart: false,
        camera: false,
        animation: false,
    };

    const raw = localStorage.getItem(STORAGE_COLLAPSE_KEY);
    if (!raw) {
        return fallback;
    }

    try {
        const parsed = JSON.parse(raw) as Partial<Record<SandboxPanelId, unknown>>;
        return {
            control: Boolean(parsed.control),
            chart: Boolean(parsed.chart),
            camera: Boolean(parsed.camera),
            animation: Boolean(parsed.animation),
        };
    } catch {
        return fallback;
    }
};

const panelLayout = ref<Layout>(readStoredLayout());
const collapsedPanels = ref<Record<SandboxPanelId, boolean>>(readCollapsedPanels());
const gridContainerRef = ref<HTMLElement | null>(null);
const gridRowHeight = ref(20);

for (const panelId of panelIds) {
    const item = panelLayout.value.find((entry) => String(entry.i) === panelId);
    if (item && item.h > COLLAPSED_PANEL_HEIGHT) {
        expandedHeights.value[panelId] = item.h;
    }
}

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

const isPanelCollapsed = (panelId: SandboxPanelId): boolean => {
    return collapsedPanels.value[panelId];
};

const mergeLayoutWithMeta = (layout: Layout): Layout => {
    return panelIds.map((panelId) => {
        const meta = defaultPanelMeta[panelId];
        const item = layout.find((entry) => String(entry.i) === panelId);
        const isCollapsed = collapsedPanels.value[panelId];

        const currentHeight = item?.h ?? meta.defaultH;
        if (!isCollapsed && currentHeight > COLLAPSED_PANEL_HEIGHT) {
            expandedHeights.value[panelId] = currentHeight;
        }

        return {
            i: panelId,
            x: item?.x ?? meta.defaultX,
            y: item?.y ?? meta.defaultY,
            w: Math.max(meta.minW, item?.w ?? meta.defaultW),
            h: isCollapsed ? COLLAPSED_PANEL_HEIGHT : Math.max(meta.minH, item?.h ?? expandedHeights.value[panelId]),
            minW: meta.minW,
            minH: isCollapsed ? COLLAPSED_PANEL_HEIGHT : meta.minH,
        };
    });
};

const persistLayoutState = () => {
    localStorage.setItem(STORAGE_LAYOUT_KEY, JSON.stringify(panelLayout.value));
    localStorage.setItem(STORAGE_COLLAPSE_KEY, JSON.stringify(collapsedPanels.value));
};

const togglePanelCollapsed = (panelId: SandboxPanelId) => {
    const item = panelLayout.value.find((entry) => String(entry.i) === panelId);
    if (!item) {
        return;
    }

    if (!collapsedPanels.value[panelId] && item.h > COLLAPSED_PANEL_HEIGHT) {
        expandedHeights.value[panelId] = item.h;
    }

    collapsedPanels.value = {
        ...collapsedPanels.value,
        [panelId]: !collapsedPanels.value[panelId],
    };

    panelLayout.value = mergeLayoutWithMeta(panelLayout.value);
};

const resetLayout = () => {
    collapsedPanels.value = {
        control: false,
        chart: false,
        camera: false,
        animation: false,
    };
    expandedHeights.value = { ...defaultExpandedHeights };
    panelLayout.value = makeDefaultLayout();
};

const handleLayoutUpdate = (layout: Layout) => {
    panelLayout.value = mergeLayoutWithMeta(layout);
};

watch(panelLayout, persistLayoutState, { deep: true });
watch(collapsedPanels, persistLayoutState, { deep: true });

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
        <v-card-title class="text-h6">{{ t('dashboard.ongoing_experiment') }}</v-card-title>

        <v-card-text class="pt-2">
            <v-alert type="info" variant="tonal" class="sandbox-debug-alert">
                <div class="text-caption">{{ isSocketOnline ? 'WebSocket online.' : 'WebSocket offline. Pulling stream buffer.' }}</div>
            </v-alert>

            <v-alert v-if="statusMessage" type="info" variant="tonal" class="sandbox-debug-alert mt-2">
                <div class="text-caption">{{ statusMessage }}</div>
            </v-alert>

            <v-alert v-if="warningMessage" type="warning" variant="tonal" class="sandbox-debug-alert mt-2">
                <div class="text-caption">{{ warningMessage }}</div>
            </v-alert>

            <v-alert v-if="!isReservationActive" type="warning" variant="tonal" class="mt-3">
                Reservation has ended. Dashboard updates automatically when next reservation becomes active.
            </v-alert>

            <template v-else>
                <v-card variant="outlined" class="sandbox-filter-card">
                    <v-card-title class="text-subtitle-2">Panel controls</v-card-title>
                    <v-card-text class="pb-2">
                        <div class="sandbox-filter-grid">
                            <v-btn
                                v-for="panelId in panelIds"
                                :key="`toggle-${panelId}`"
                                size="small"
                                variant="tonal"
                                class="sandbox-no-drag"
                                :prepend-icon="isPanelCollapsed(panelId) ? 'mdi-arrow-expand-vertical' : 'mdi-arrow-collapse-vertical'"
                                @click="togglePanelCollapsed(panelId)"
                            >
                                {{ isPanelCollapsed(panelId) ? `Expand ${panelTitles[panelId]}` : `Collapse ${panelTitles[panelId]}` }}
                            </v-btn>
                        </div>

                        <div class="sandbox-filter-actions">
                            <v-btn size="small" variant="tonal" prepend-icon="mdi-backup-restore" class="sandbox-no-drag" @click="resetLayout">
                                Reset layout
                            </v-btn>
                        </div>
                    </v-card-text>
                </v-card>

                <div ref="gridContainerRef" class="sandbox-grid-host">
                    <GridLayout
                        :layout="panelLayout"
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
                            v-for="item in panelLayout"
                            :key="String(item.i)"
                            :x="item.x"
                            :y="item.y"
                            :w="item.w"
                            :h="item.h"
                            :i="item.i"
                            :min-w="item.minW ?? 4"
                            :min-h="item.minH ?? COLLAPSED_PANEL_HEIGHT"
                            :is-resizable="!isPanelCollapsed(itemPanelId(item.i))"
                            drag-ignore-from=".sandbox-no-drag, button, input, textarea, select, .v-field, .v-btn, .v-input, .v-selection-control"
                            class="sandbox-grid-item"
                        >
                            <v-card
                                variant="outlined"
                                :class="[
                                    'sandbox-section-card d-flex flex-column w-100',
                                    { 'sandbox-section-card--collapsed': isPanelCollapsed(itemPanelId(item.i)) },
                                ]"
                            >
                                <div class="sandbox-panel-handle sandbox-section-header">
                                    <div class="sandbox-section-title">
                                        <v-icon :icon="panelIcons[itemPanelId(item.i)]" size="18" />
                                        <span class="text-subtitle-1">{{ panelTitles[itemPanelId(item.i)] }}</span>
                                    </div>
                                    <div class="sandbox-section-actions sandbox-no-drag">
                                        <v-btn
                                            size="small"
                                            variant="text"
                                            class="sandbox-no-drag"
                                            :icon="isPanelCollapsed(itemPanelId(item.i)) ? 'mdi-chevron-down' : 'mdi-chevron-up'"
                                            @click.stop="togglePanelCollapsed(itemPanelId(item.i))"
                                        />
                                    </div>
                                </div>

                                <v-expand-transition>
                                    <v-card-text v-if="!isPanelCollapsed(itemPanelId(item.i))" class="sandbox-section-body d-flex flex-column grow">
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
                                            <v-alert v-if="props.resolvingCameraTarget" type="info" variant="tonal"
                                                >Resolving camera target...</v-alert
                                            >
                                            <v-alert v-else-if="!props.cameraDeviceName || !props.cameraServerId" type="warning" variant="tonal">
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

                                        <div v-else class="animation-placeholder-wrapper">
                                            <!-- TODO: Replace placeholder with animation component once API and asset contract are finalized. -->
                                            <div class="animation-placeholder">
                                                <v-icon icon="mdi-chart-timeline-variant" size="42" class="mb-2" />
                                                <div class="text-body-2">Animation placeholder</div>
                                            </div>
                                        </div>
                                    </v-card-text>
                                </v-expand-transition>
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

.sandbox-filter-card {
    margin-bottom: 12px;
}

.sandbox-debug-alert {
    overflow-wrap: anywhere;
    word-break: break-word;
}

.sandbox-filter-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 8px 12px;
}

.sandbox-filter-actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 8px;
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

.sandbox-section-card--collapsed {
    border-style: dashed;
}

.sandbox-section-header {
    display: flex;
    justify-content: space-between;
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

.sandbox-section-actions {
    display: flex;
    align-items: center;
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
.sandbox-camera-panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
    flex: 1 1 auto;
    min-height: 0;
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

.sandbox-grid-layout :deep(.vgl-item.vgl-item--placeholder) {
    border-radius: 10px;
    background: rgba(var(--v-theme-primary), 0.14);
}

@media (max-width: 960px) {
    .sandbox-grid-layout {
        min-height: 640px;
    }
}
</style>
