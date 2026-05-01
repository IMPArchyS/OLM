<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { Command, type DeviceType, type Reservation } from '@/types/api';
import type { ExperimentFormData } from '@/types/forms';
import { useExperiments } from '@/composables/useExperiments';
import { useReservationStream } from '@/composables/useReservationStream';
import { useAuthStore } from '@/stores/auth';
import { useToastStore } from '@/stores/toast';
import { useI18n } from 'vue-i18n';
import { useSandboxLayout, type SandboxPanelId, type PanelMeta } from '@/composables/useSandboxLayout';
import { useSandboxGridSize } from '@/composables/useSandboxGridSize';
import SandboxMobileLayout from './SandboxMobileLayout.vue';
import SandboxDesktopGrid from './SandboxDesktopGrid.vue';

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
const { outputHistory, activate, deactivate, sendCommand } = useReservationStream();

const panelIds: SandboxPanelId[] = ['control', 'chart', 'camera', 'animation'];

const defaultPanelMeta: Record<SandboxPanelId, PanelMeta> = {
    control: { title: t('dashboard.experimentControl'), icon: 'mdi-tune-vertical-variant', minW: 3, minH: 24, defaultW: 6, defaultH: 30, defaultX: 0, defaultY: 0 },
    chart: { title: t('dashboard.liveOutput'), icon: 'mdi-chart-line', minW: 3, minH: 20, defaultW: 6, defaultH: 20, defaultX: 6, defaultY: 0 },
    camera: { title: t('dashboard.cameraStream'), icon: 'mdi-video-wireless', minW: 3, minH: 20, defaultW: 6, defaultH: 20, defaultX: 0, defaultY: 30 },
    animation: { title: t('dashboard.animation'), icon: 'mdi-chart-timeline-variant', minW: 3, minH: 20, defaultW: 6, defaultH: 20, defaultX: 6, defaultY: 20 },
};

const { panelVisibility, collapsedPanels, visiblePanelLayout, resetLayout, setPanelVisibility, toggleCollapse, handleLayoutUpdate } =
    useSandboxLayout(panelIds, defaultPanelMeta);

const { gridContainerRef, isMobile, gridRowHeight, gridHeight } = useSandboxGridSize();

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

const canRunExperiment = computed(() => experimentsByDevice.value.length > 0 && formData.value.id !== null);
const deviceVisualConfig = computed(() => props.deviceType?.visual_config ?? null);

const sharedPanelProps = computed(() => ({
    loading: loading.value,
    experimentsByDevice: experimentsByDevice.value,
    selectedDeviceId: props.reservation.device_id,
    outputHistory: outputHistory.value,
    resolvingCameraTarget: props.resolvingCameraTarget,
    cameraDeviceName: props.cameraDeviceName,
    cameraServerId: props.cameraServerId,
    visualConfig: deviceVisualConfig.value,
    canRunExperiment: canRunExperiment.value,
}));

onBeforeRouteLeave(() => { deactivate(); });
onBeforeUnmount(() => { deactivate(); });

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
    if (!accessToken) return;
    activate(accessToken);
});
</script>

<template>
    <v-card class="sandbox-shell" variant="flat">
        <div class="sandbox-toolbar">
            <div class="sandbox-toolbar-controls sandbox-no-drag">
                <div class="sandbox-toolbar-toggles">
                    <v-checkbox
                        v-for="panelId in panelIds"
                        :key="`toggle-${panelId}`"
                        :model-value="panelVisibility[panelId]"
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
                    {{ t('dashboard.resetLayout') }}
                </v-btn>
            </div>
        </div>

        <div class="sandbox-body">
            <div ref="gridContainerRef" class="sandbox-grid-host">
                <SandboxMobileLayout
                    v-if="isMobile"
                    :panel-ids="panelIds"
                    :panel-meta="defaultPanelMeta"
                    :panel-visibility="panelVisibility"
                    v-bind="sharedPanelProps"
                    @set-visibility="setPanelVisibility"
                    @update:formData="formData = $event"
                    @run="runExperiment"
                />
                <SandboxDesktopGrid
                    v-else
                    :layout="visiblePanelLayout"
                    :row-height="gridRowHeight"
                    :height="gridHeight"
                    :panel-meta="defaultPanelMeta"
                    :collapsed-panels="collapsedPanels"
                    v-bind="sharedPanelProps"
                    @update:layout="(layout) => handleLayoutUpdate(layout, isMobile)"
                    @toggle-collapse="toggleCollapse"
                    @set-visibility="setPanelVisibility"
                    @update:formData="formData = $event"
                    @run="runExperiment"
                />
            </div>
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
</style>
