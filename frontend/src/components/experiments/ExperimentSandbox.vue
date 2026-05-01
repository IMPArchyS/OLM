<script setup lang="ts">
import { useResizeObserver } from '@vueuse/core';
import { GridItem, GridLayout, type Layout } from 'grid-layout-plus';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { Command, type DeviceType, type Reservation } from '@/types/api';
import type { ExperimentFormData } from '@/types/forms';
import { useExperiments } from '@/composables/useExperiments';
import { useReservationStream } from '@/composables/useReservationStream';
import { useAuthStore } from '@/stores/auth';
import { useToastStore } from '@/stores/toast';
import SandboxPanelContent from './SandboxPanelContent.vue';

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

const authStore = useAuthStore();
const toast = useToastStore();
const { experimentsByDevice, loading, fetchExperimentsByDevice } = useExperiments();
const { outputHistory, activate, deactivate, sendCommand, isReservationActive } = useReservationStream();

type SandboxPanelId = 'control' | 'chart' | 'camera' | 'animation';

const STORAGE_LAYOUT_KEY = 'olm:sandbox:grid-layout:v2';
const STORAGE_VISIBILITY_KEY = 'olm:sandbox:grid-visibility:v1';
const MOBILE_BREAKPOINT = 960;
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
        minW: 3,
        minH: 24,
        defaultW: 6,
        defaultH: 30,
        defaultX: 0,
        defaultY: 0,
    },
    chart: {
        title: 'Live output',
        icon: 'mdi-chart-line',
        minW: 3,
        minH: 20,
        defaultW: 6,
        defaultH: 20,
        defaultX: 6,
        defaultY: 0,
    },
    camera: {
        title: 'Camera stream',
        icon: 'mdi-video-wireless',
        minW: 3,
        minH: 20,
        defaultW: 6,
        defaultH: 20,
        defaultX: 0,
        defaultY: 30,
    },
    animation: {
        title: 'Experiment animation',
        icon: 'mdi-chart-timeline-variant',
        minW: 3,
        minH: 20,
        defaultW: 6,
        defaultH: 20,
        defaultX: 6,
        defaultY: 20,
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

const COLLAPSED_H = 6;

const panelLayout = ref<Layout>(readStoredLayout());
const panelVisibility = ref<Record<SandboxPanelId, boolean>>(readPanelVisibility());
const collapsedPanels = ref<Record<SandboxPanelId, boolean>>({ control: false, chart: false, camera: false, animation: false });
const savedHeights = ref<Record<SandboxPanelId, number>>({
    control: defaultPanelMeta.control.defaultH,
    chart: defaultPanelMeta.chart.defaultH,
    camera: defaultPanelMeta.camera.defaultH,
    animation: defaultPanelMeta.animation.defaultH,
});
const gridContainerRef = ref<HTMLElement | null>(null);
const isMobile = ref(false);
const gridRowHeight = ref(10);
const gridHeight = ref(600);

const updateGridHeight = () => {
    const el = gridContainerRef.value;
    if (!el) return;
    const top = el.getBoundingClientRect().top;
    gridHeight.value = Math.max(400, window.innerHeight - top - 32);
};

const itemPanelId = (itemId: number | string): SandboxPanelId => {
    return String(itemId) as SandboxPanelId;
};

const isPanelVisible = (panelId: SandboxPanelId): boolean => {
    return panelVisibility.value[panelId];
};

const isPanelCollapsed = (panelId: SandboxPanelId): boolean => {
    return collapsedPanels.value[panelId];
};

const setPanelVisibility = (panelId: SandboxPanelId, visible: boolean) => {
    panelVisibility.value = {
        ...panelVisibility.value,
        [panelId]: visible,
    };
};

const toggleCollapse = (panelId: SandboxPanelId) => {
    const isCollapsed = collapsedPanels.value[panelId];

    if (isCollapsed) {
        panelLayout.value = panelLayout.value.map((item) =>
            String(item.i) === panelId
                ? { ...item, h: savedHeights.value[panelId] ?? defaultPanelMeta[panelId].defaultH, minH: defaultPanelMeta[panelId].minH }
                : item,
        );
    } else {
        const current = panelLayout.value.find((item) => String(item.i) === panelId);
        if (current) {
            savedHeights.value = { ...savedHeights.value, [panelId]: current.h };
        }
        panelLayout.value = panelLayout.value.map((item) =>
            String(item.i) === panelId ? { ...item, h: COLLAPSED_H, minH: COLLAPSED_H } : item,
        );
    }

    collapsedPanels.value = { ...collapsedPanels.value, [panelId]: !isCollapsed };
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
    panelVisibility.value = { control: true, chart: true, camera: true, animation: true };
    collapsedPanels.value = { control: false, chart: false, camera: false, animation: false };
    panelLayout.value = makeDefaultLayout();
};

const handleLayoutUpdate = (layout: Layout) => {
    if (isMobile.value) {
        return;
    }

    const layoutById = new Map(layout.map((entry) => [String(entry.i), entry]));
    const merged = panelLayout.value.map((entry) => layoutById.get(String(entry.i)) ?? entry);

    panelLayout.value = panelIds.map((panelId) => {
        const meta = defaultPanelMeta[panelId];
        const item = merged.find((entry) => String(entry.i) === panelId);
        const isCollapsed = collapsedPanels.value[panelId];
        const w = Math.min(Math.max(meta.minW, item?.w ?? meta.defaultW), 12);
        const x = Math.max(0, Math.min(item?.x ?? meta.defaultX, 12 - w));

        return {
            i: panelId,
            x,
            y: item?.y ?? meta.defaultY,
            w,
            h: isCollapsed ? COLLAPSED_H : Math.max(meta.minH, item?.h ?? meta.defaultH),
            minW: meta.minW,
            minH: isCollapsed ? COLLAPSED_H : meta.minH,
        };
    });
};

watch(panelLayout, persistLayoutState, { deep: true });
watch(panelVisibility, persistLayoutState, { deep: true });

useResizeObserver(gridContainerRef, (entries) => {
    const width = entries[0]?.contentRect.width ?? 0;
    isMobile.value = width > 0 && width <= MOBILE_BREAKPOINT;
    if (width < 700) {
        gridRowHeight.value = 8;
    } else if (width < 960) {
        gridRowHeight.value = 9;
    } else {
        gridRowHeight.value = 10;
    }
    updateGridHeight();
});

const formData = ref<ExperimentFormData>({
    user_id: authStore.user?.id ?? null,
    id: null,
    command: Command.START,
    input_arguments: {},
    output_arguments: [],
    setpoint_changes: {},
    device_id: null,
    software_name: null,
    simulation_time: 0,
    sample_rate: 0,
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
    window.removeEventListener('resize', updateGridHeight);
});

function runExperiment() {
    const selectedExperiment = experimentsByDevice.value.find((exp) => exp.id === formData.value.id);
    formData.value.output_arguments = selectedExperiment?.output_arguments ?? [];

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
    updateGridHeight();
    window.addEventListener('resize', updateGridHeight);
});

const handleFormDataUpdate = (data: typeof formData.value) => {
    formData.value = data;
};
</script>

<template>
    <v-card class="sandbox-shell" variant="flat">
        <div class="sandbox-toolbar">
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
                                <v-icon :icon="defaultPanelMeta[panelId].icon" size="14" />
                                <span class="text-caption">{{ defaultPanelMeta[panelId].title }}</span>
                            </div>
                        </template>
                    </v-checkbox>
                </div>

                <v-btn size="x-small" variant="tonal" prepend-icon="mdi-backup-restore" class="sandbox-no-drag" @click="resetLayout">
                    Reset layout
                </v-btn>
            </div>
        </div>

        <div class="sandbox-body">
            <v-alert v-if="!isReservationActive" type="warning" variant="tonal" density="compact" class="sandbox-reservation-alert mb-2">
                Reservation has ended. Dashboard updates automatically when next reservation becomes active.
            </v-alert>

            <template v-else>
                <v-alert v-if="visiblePanelLayout.length === 0" density="compact" variant="tonal" type="info" class="mb-2">
                    No panels enabled. Use panel controls to toggle panels on.
                </v-alert>

                <div ref="gridContainerRef" class="sandbox-grid-host">
                    <!-- Mobile: simple stacked layout, no drag/resize -->
                    <div v-if="isMobile" class="sandbox-mobile-layout">
                        <template v-for="panelId in panelIds" :key="panelId">
                            <v-card v-if="isPanelVisible(panelId)" variant="outlined" class="sandbox-section-card">
                                <div class="sandbox-section-header">
                                    <div class="sandbox-section-title">
                                        <v-icon :icon="defaultPanelMeta[panelId].icon" size="18" />
                                        <span class="text-subtitle-1">{{ defaultPanelMeta[panelId].title }}</span>
                                    </div>
                                    <v-btn
                                        icon="mdi-close"
                                        size="x-small"
                                        variant="text"
                                        density="compact"
                                        @click="setPanelVisibility(panelId, false)"
                                    />
                                </div>

                                <v-card-text class="sandbox-section-body d-flex flex-column grow">
                                    <SandboxPanelContent
                                        :panel-id="panelId"
                                        :loading="loading"
                                        :experiments-by-device="experimentsByDevice"
                                        :selected-device-id="props.reservation.device_id"
                                        :output-history="outputHistory"
                                        :resolving-camera-target="props.resolvingCameraTarget"
                                        :camera-device-name="props.cameraDeviceName"
                                        :camera-server-id="props.cameraServerId"
                                        :visual-config="deviceVisualConfig"
                                        :can-run-experiment="canRunExperiment"
                                        @update:formData="handleFormDataUpdate"
                                        @run="runExperiment"
                                    />
                                </v-card-text>
                            </v-card>
                        </template>
                    </div>

                    <!-- Desktop: drag/resize grid layout -->
                    <GridLayout
                        v-else
                        :layout="visiblePanelLayout"
                        :col-num="12"
                        :row-height="gridRowHeight"
                        :margin="[0, 0]"
                        :container-padding="[0, 0]"
                        :is-draggable="true"
                        :is-resizable="true"
                        :is-bounded="true"
                        :use-css-transforms="true"
                        :vertical-compact="false"
                        :style="{ height: gridHeight + 'px' }"
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
                            :min-w="item.minW ?? 3"
                            :min-h="item.minH ?? defaultPanelMeta[itemPanelId(item.i)].minH"
                            :is-resizable="true"
                            drag-ignore-from=".sandbox-no-drag, button, input, textarea, select, .v-field, .v-btn, .v-input, .v-selection-control, .sandbox-animation-panel, .sandbox-animation-panel *"
                            class="sandbox-grid-item"
                        >
                            <v-card variant="outlined" class="sandbox-section-card d-flex flex-column w-100">
                                <div :class="['sandbox-panel-handle sandbox-section-header', { 'sandbox-section-header--collapsed': isPanelCollapsed(itemPanelId(item.i)) }]">
                                    <div class="sandbox-section-title">
                                        <v-icon :icon="defaultPanelMeta[itemPanelId(item.i)].icon" size="18" />
                                        <span class="text-subtitle-1">{{ defaultPanelMeta[itemPanelId(item.i)].title }}</span>
                                    </div>
                                    <div class="d-flex align-center ga-1 sandbox-no-drag">
                                        <v-btn
                                            :icon="isPanelCollapsed(itemPanelId(item.i)) ? 'mdi-chevron-down' : 'mdi-chevron-up'"
                                            size="small"
                                            variant="text"
                                            @click="toggleCollapse(itemPanelId(item.i))"
                                        />
                                        <v-btn
                                            icon="mdi-close"
                                            size="small"
                                            variant="text"
                                            @click="setPanelVisibility(itemPanelId(item.i), false)"
                                        />
                                    </div>
                                </div>

                                <v-card-text v-show="!isPanelCollapsed(itemPanelId(item.i))" class="sandbox-section-body d-flex flex-column grow">
                                    <SandboxPanelContent
                                        :panel-id="itemPanelId(item.i)"
                                        :loading="loading"
                                        :experiments-by-device="experimentsByDevice"
                                        :selected-device-id="props.reservation.device_id"
                                        :output-history="outputHistory"
                                        :resolving-camera-target="props.resolvingCameraTarget"
                                        :camera-device-name="props.cameraDeviceName"
                                        :camera-server-id="props.cameraServerId"
                                        :visual-config="deviceVisualConfig"
                                        :can-run-experiment="canRunExperiment"
                                        fill-container
                                        @update:formData="handleFormDataUpdate"
                                        @run="runExperiment"
                                    />
                                </v-card-text>
                            </v-card>
                        </GridItem>
                    </GridLayout>
                </div>
            </template>
        </div>
    </v-card>
</template>

<style scoped>
.sandbox-shell {
    width: 100%;
    overflow: visible;
}

.sandbox-toolbar {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 4px 8px;
    margin-bottom: 4px;
}

.sandbox-body {
    min-width: 0;
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

.sandbox-reservation-alert :deep(.v-alert__content) {
    font-size: 13px;
}

.sandbox-grid-host {
    width: 100%;
}

/* Mobile stacked layout */
.sandbox-mobile-layout {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.sandbox-mobile-layout .sandbox-section-card {
    overflow: hidden;
}

.sandbox-mobile-layout .sandbox-chart-panel,
.sandbox-mobile-layout .sandbox-camera-panel,
.sandbox-mobile-layout .sandbox-animation-panel {
    min-height: 280px;
}

/* Desktop grid layout */
.sandbox-grid-layout {
    border-radius: 12px;
    background: rgba(var(--v-theme-surface-variant), 0.2);
    padding: 0;
    overflow: hidden;
}

.sandbox-grid-item {
    box-sizing: border-box;
    padding: 4px;
    min-height: 0;
}

.sandbox-section-card {
    height: 100%;
    overflow: hidden;
}

.sandbox-section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
    cursor: move;
    transition: padding 0.15s ease;
}

.sandbox-section-header--collapsed {
    padding: 5px 10px;
}

.sandbox-mobile-layout .sandbox-section-header {
    cursor: default;
}

.sandbox-section-title {
    display: flex;
    align-items: center;
    gap: 8px;
}

.sandbox-section-body {
    min-height: 0;
    overflow: hidden;
    padding: 0 !important;
}

.sandbox-panel-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
    flex: 1 1 auto;
    padding: 12px 16px;
    overflow: auto;
}

.sandbox-chart-panel,
.sandbox-camera-panel,
.sandbox-animation-panel {
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    min-height: 0;
    height: 100%;
    padding: 8px;
}

.sandbox-camera-panel :deep(.camera-view),
.sandbox-chart-panel :deep(.simple-output-chart),
.sandbox-animation-panel :deep(.device-animation-panel) {
    flex: 1 1 auto;
}

.sandbox-camera-panel :deep(.camera-content) {
    padding: 0;
}

.sandbox-grid-layout :deep(.vgl-item.vgl-item--placeholder) {
    border-radius: 10px;
    background: rgba(var(--v-theme-primary), 0.14);
}
</style>
