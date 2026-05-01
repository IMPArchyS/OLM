<script setup lang="ts">
import type { Experiment, DeviceVisualConfig } from '@/types/api';
import type { ExperimentFormData } from '@/types/forms';
import type { SandboxPanelId, PanelMeta } from '@/composables/useSandboxLayout';
import SandboxPanelContent from './SandboxPanelContent.vue';

interface Props {
    panelIds: SandboxPanelId[];
    panelMeta: Record<SandboxPanelId, PanelMeta>;
    panelVisibility: Record<SandboxPanelId, boolean>;
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
    'set-visibility': [panelId: SandboxPanelId, value: boolean];
    'update:formData': [data: ExperimentFormData];
    run: [];
}>();
</script>

<template>
    <div class="sandbox-mobile-layout">
        <template v-for="panelId in props.panelIds" :key="panelId">
            <v-card v-if="props.panelVisibility[panelId]" variant="outlined" class="sandbox-section-card">
                <div class="sandbox-section-header">
                    <div class="sandbox-section-title">
                        <v-icon :icon="props.panelMeta[panelId].icon" size="18" />
                        <span class="text-subtitle-1">{{ props.panelMeta[panelId].title }}</span>
                    </div>
                    <v-btn
                        icon="mdi-close"
                        size="x-small"
                        variant="text"
                        density="compact"
                        @click="emit('set-visibility', panelId, false)"
                    />
                </div>

                <v-card-text class="sandbox-section-body d-flex flex-column grow">
                    <SandboxPanelContent
                        :panel-id="panelId"
                        :loading="props.loading"
                        :experiments-by-device="props.experimentsByDevice"
                        :selected-device-id="props.selectedDeviceId"
                        :output-history="props.outputHistory"
                        :resolving-camera-target="props.resolvingCameraTarget"
                        :camera-device-name="props.cameraDeviceName"
                        :camera-server-id="props.cameraServerId"
                        :visual-config="props.visualConfig"
                        :can-run-experiment="props.canRunExperiment"
                        @update:formData="emit('update:formData', $event)"
                        @run="emit('run')"
                    />
                </v-card-text>
            </v-card>
        </template>
    </div>
</template>

<style scoped>
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
</style>
