<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { Experiment, DeviceVisualConfig } from '@/types/api';
import type { ExperimentFormData } from '@/types/forms';
import type { SandboxPanelId } from '@/composables/useSandboxLayout';
import ExperimentSelector from './ExperimentSelector.vue';
import SimpleOutputChart from './SimpleOutputChart.vue';
import CameraView from '@/components/dashboard/CameraView.vue';
import DeviceAnimationPanel from './DeviceAnimationPanel.vue';
type OutputRow = Record<string, unknown>;

interface Props {
    panelId: SandboxPanelId;
    loading: boolean;
    experimentsByDevice: Experiment[];
    selectedDeviceId: number;
    outputHistory: OutputRow[];
    resolvingCameraTarget: boolean;
    cameraDeviceName: string;
    cameraServerId: number;
    visualConfig: DeviceVisualConfig | null;
    canRunExperiment: boolean;
    fillContainer?: boolean;
}

withDefaults(defineProps<Props>(), {
    fillContainer: false,
});

const emit = defineEmits<{
    'update:formData': [data: ExperimentFormData];
    run: [];
}>();

const { t } = useI18n();
</script>

<template>
    <div v-if="panelId === 'control'" class="sandbox-panel-content">
        <ExperimentSelector
            fixed-command=""
            :loading="loading"
            :experiments="experimentsByDevice"
            :selected-device-id="selectedDeviceId"
            compact
            @update:formData="emit('update:formData', $event)"
        />
        <v-btn color="info" prepend-icon="mdi-play" :disabled="!canRunExperiment" @click="emit('run')">
            {{ t('dashboard.run_experiment') }}
        </v-btn>
    </div>

    <div v-else-if="panelId === 'chart'" class="sandbox-chart-panel">
        <SimpleOutputChart
            :output-history="outputHistory"
            hide-title
            compact
            :x-label="t('dashboard.xLabel')"
            :y-label="t('dashboard.yLabel')"
            :height="fillContainer ? 240 : 280"
            :fill-container="fillContainer"
            class="h-100"
        />
    </div>

    <div v-else-if="panelId === 'camera'" class="sandbox-camera-panel">
        <v-alert v-if="resolvingCameraTarget" type="info" variant="tonal" density="compact"> Resolving camera target... </v-alert>
        <v-alert v-else-if="!cameraDeviceName || !cameraServerId" type="warning" variant="tonal" density="compact">
            Unable to resolve server/device for camera stream from this reservation.
        </v-alert>
        <CameraView v-else :device_name="cameraDeviceName" :server_id="cameraServerId" compact hide-title class="h-100" />
    </div>

    <div v-else class="sandbox-animation-panel">
        <DeviceAnimationPanel :visual-config="visualConfig" :output-history="outputHistory" class="h-100" />
    </div>
</template>
