<script setup lang="ts">
import { GridItem, GridLayout, type Layout } from 'grid-layout-plus';
import type { Experiment, DeviceVisualConfig } from '@/types/api';
import type { ExperimentFormData } from '@/types/forms';
import type { SandboxPanelId, PanelMeta } from '@/composables/useSandboxLayout';
import SandboxPanelContent from './SandboxPanelContent.vue';

interface Props {
    layout: Layout;
    rowHeight: number;
    height: number;
    panelMeta: Record<SandboxPanelId, PanelMeta>;
    collapsedPanels: Record<SandboxPanelId, boolean>;
    loading: boolean;
    experimentsByDevice: Experiment[];
    selectedDeviceId: number;
    outputHistory: Record<string, unknown>[];
    resolvingCameraTarget: boolean;
    cameraDeviceName: string;
    cameraServerId: number;
    visualConfig: DeviceVisualConfig | null;
    canRunExperiment: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
    'update:layout': [layout: Layout];
    'toggle-collapse': [panelId: SandboxPanelId];
    'set-visibility': [panelId: SandboxPanelId, value: boolean];
    'update:formData': [data: ExperimentFormData];
    run: [];
}>();

const itemPanelId = (itemId: number | string): SandboxPanelId => String(itemId) as SandboxPanelId;
</script>

<template>
    <GridLayout
        :layout="props.layout"
        :col-num="12"
        :row-height="props.rowHeight"
        :margin="[0, 0]"
        :container-padding="[0, 0]"
        :is-draggable="true"
        :is-resizable="true"
        :is-bounded="true"
        :use-css-transforms="true"
        :vertical-compact="false"
        :style="{ height: props.height + 'px' }"
        class="sandbox-grid-layout"
        @update:layout="emit('update:layout', $event)"
    >
        <GridItem
            v-for="item in props.layout"
            :key="String(item.i)"
            :x="item.x"
            :y="item.y"
            :w="item.w"
            :h="item.h"
            :i="item.i"
            :min-w="item.minW ?? 3"
            :min-h="item.minH ?? props.panelMeta[itemPanelId(item.i)].minH"
            :is-resizable="true"
            drag-ignore-from=".sandbox-no-drag, button, input, textarea, select, .v-field, .v-btn, .v-input, .v-selection-control, .sandbox-animation-panel, .sandbox-animation-panel *"
            class="sandbox-grid-item"
        >
            <v-card variant="outlined" class="sandbox-section-card d-flex flex-column w-100">
                <div
                    :class="[
                        'sandbox-panel-handle sandbox-section-header',
                        { 'sandbox-section-header--collapsed': props.collapsedPanels[itemPanelId(item.i)] },
                    ]"
                >
                    <div class="sandbox-section-title">
                        <v-icon :icon="props.panelMeta[itemPanelId(item.i)].icon" size="18" />
                        <span class="text-subtitle-1">{{ props.panelMeta[itemPanelId(item.i)].title }}</span>
                    </div>
                    <div class="d-flex align-center ga-1 sandbox-no-drag">
                        <v-btn
                            :icon="props.collapsedPanels[itemPanelId(item.i)] ? 'mdi-chevron-down' : 'mdi-chevron-up'"
                            size="small"
                            variant="text"
                            @click="emit('toggle-collapse', itemPanelId(item.i))"
                        />
                        <v-btn
                            icon="mdi-close"
                            size="small"
                            variant="text"
                            @click="emit('set-visibility', itemPanelId(item.i), false)"
                        />
                    </div>
                </div>

                <v-card-text
                    v-show="!props.collapsedPanels[itemPanelId(item.i)]"
                    class="sandbox-section-body d-flex flex-column grow"
                >
                    <SandboxPanelContent
                        :panel-id="itemPanelId(item.i)"
                        :loading="props.loading"
                        :experiments-by-device="props.experimentsByDevice"
                        :selected-device-id="props.selectedDeviceId"
                        :output-history="props.outputHistory"
                        :resolving-camera-target="props.resolvingCameraTarget"
                        :camera-device-name="props.cameraDeviceName"
                        :camera-server-id="props.cameraServerId"
                        :visual-config="props.visualConfig"
                        :can-run-experiment="props.canRunExperiment"
                        fill-container
                        @update:formData="emit('update:formData', $event)"
                        @run="emit('run')"
                    />
                </v-card-text>
            </v-card>
        </GridItem>
    </GridLayout>
</template>

<style scoped>
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
