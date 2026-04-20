<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import ExperimentSelector from '@/components/experiments/ExperimentSelector.vue';
import { useI18n } from 'vue-i18n';
import { Command, type Device, type ExperimentLog } from '@/types/api';
import type { QueueFormData } from '@/types/forms';
import { useExperiments } from '@/composables/useExperiments';
import { useDevices } from '@/composables/useDevices';
import { useExperimentLogs } from '@/composables/useExperimentLogs';
import { useAuthStore } from '@/stores/auth';
import { useToastStore } from '@/stores/toast';

const { t } = useI18n();
const toast = useToastStore();
const authStore = useAuthStore();
const { experiments, loading, queueSelectedExperiment, fetchExperiments } = useExperiments();
const { availableDevices, fetchAvailableDevices } = useDevices();
const { userExperimentLogs, fetchExperimentLogsByUser } = useExperimentLogs();

type QueueTargetMode = 'same-as-last' | 'any-compatible' | 'pick-device';

const queueTargetMode = ref<QueueTargetMode>('same-as-last');
const manualDeviceId = ref<number | null>(null);

const selectableExperiments = computed(() => {
    return experiments.value.filter((experiment) => !experiment.deleted_at && (experiment.devices?.length ?? 0) > 0);
});

const selectedExperiment = computed(() => {
    if (!formData.value.id) {
        return null;
    }

    return selectableExperiments.value.find((experiment) => experiment.id === formData.value.id) ?? null;
});

const compatibleDevices = computed<Device[]>(() => {
    return (selectedExperiment.value?.devices ?? []).filter((device) => !device.deleted_at);
});

const availableDeviceIds = computed(() => {
    return new Set(availableDevices.value.map((device) => device.id));
});

const availableCompatibleDevices = computed<Device[]>(() => {
    return compatibleDevices.value.filter((device) => availableDeviceIds.value.has(device.id));
});

const queueCandidateDevices = computed<Device[]>(() => {
    return availableCompatibleDevices.value.length > 0 ? availableCompatibleDevices.value : compatibleDevices.value;
});

const sortedMatchingLogs = computed<ExperimentLog[]>(() => {
    if (!selectedExperiment.value) {
        return [];
    }

    return userExperimentLogs.value
        .filter((log) => log.experiment_id === selectedExperiment.value?.id)
        .slice()
        .sort((a, b) => {
            const aTime = a.started_at ? new Date(a.started_at).getTime() : 0;
            const bTime = b.started_at ? new Date(b.started_at).getTime() : 0;

            if (aTime !== bTime) {
                return bTime - aTime;
            }

            return b.id - a.id;
        });
});

const lastUsedDeviceId = computed<number | null>(() => {
    for (const log of sortedMatchingLogs.value) {
        if (queueCandidateDevices.value.some((device) => device.id === log.device_id)) {
            return log.device_id;
        }
    }

    return null;
});

const lastUsedDevice = computed(() => {
    if (!lastUsedDeviceId.value) {
        return null;
    }

    return queueCandidateDevices.value.find((device) => device.id === lastUsedDeviceId.value) ?? null;
});

const resolvedDeviceId = computed<number | null>(() => {
    if (queueTargetMode.value === 'same-as-last') {
        return lastUsedDeviceId.value;
    }

    if (queueTargetMode.value === 'pick-device') {
        if (!manualDeviceId.value) {
            return null;
        }

        return queueCandidateDevices.value.some((device) => device.id === manualDeviceId.value) ? manualDeviceId.value : null;
    }

    return queueCandidateDevices.value[0]?.id ?? null;
});

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
    const [experimentsResult, devicesResult] = await Promise.all([fetchExperiments(), fetchAvailableDevices()]);

    if (!experimentsResult.success) {
        toast.error(experimentsResult.message || 'Failed to fetch available experiments');
    }

    if (!devicesResult.success) {
        toast.error(devicesResult.message || 'Failed to fetch available devices');
    }

    const logsResult = await fetchExperimentLogsByUser(authStore.user?.id);
    if (!logsResult.success && authStore.user?.id) {
        toast.error(logsResult.message || 'Failed to fetch experiment logs');
    }
});

watch(
    () => selectedExperiment.value?.id ?? null,
    () => {
        manualDeviceId.value = null;

        if (lastUsedDeviceId.value) {
            queueTargetMode.value = 'same-as-last';
            return;
        }

        queueTargetMode.value = queueCandidateDevices.value.length > 0 ? 'any-compatible' : 'pick-device';
    },
);

watch(queueTargetMode, (mode) => {
    if (mode !== 'pick-device') {
        manualDeviceId.value = null;
    }
});

const handleFormDataUpdate = (data: typeof formData.value) => {
    formData.value = data;
};

const addToQueue = async () => {
    const selectedExperiment = selectableExperiments.value.find((exp) => exp.id === formData.value.id);
    formData.value.output_arguments = selectedExperiment?.output_arguments ?? [];

    const deviceId = resolvedDeviceId.value;
    if (!deviceId) {
        toast.error(t('queues.target_missing'));
        return;
    }

    formData.value.device_id = deviceId;

    console.log(JSON.stringify(formData.value, null, 2));
    const result = await queueSelectedExperiment(formData.value);

    if (result.success) {
        toast.success(result.message ?? 'queued');
        return;
    }

    toast.error(result.message ?? 'failed');
};
</script>

<template>
    <v-card class="queue-card">
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ t('queues.title') }}</span>
        </v-card-title>
        <v-card-text class="queue-card__body">
            <div class="queue-layout">
                <ExperimentSelector
                    fixed-command="start"
                    :loading="loading"
                    :experiments="selectableExperiments"
                    :selected-device-id="resolvedDeviceId"
                    compact
                    class="queue-field"
                    @update:formData="handleFormDataUpdate"
                />

                <v-card variant="outlined" class="queue-target-card">
                    <v-card-title class="text-subtitle-2">{{ t('queues.target_strategy_title') }}</v-card-title>
                    <v-card-text class="pt-1">
                        <v-radio-group v-model="queueTargetMode" density="compact" hide-details>
                            <v-radio :label="t('queues.target_same_last')" value="same-as-last" :disabled="!lastUsedDeviceId" />
                            <v-radio :label="t('queues.target_any')" value="any-compatible" :disabled="queueCandidateDevices.length === 0" />
                            <v-radio :label="t('queues.target_manual')" value="pick-device" :disabled="queueCandidateDevices.length === 0" />
                        </v-radio-group>

                        <v-alert
                            v-if="queueTargetMode === 'same-as-last' && lastUsedDevice"
                            type="info"
                            variant="tonal"
                            density="compact"
                            class="mt-3"
                        >
                            {{ t('queues.last_device_label') }}: {{ lastUsedDevice.name }} (ID {{ lastUsedDevice.id }})
                        </v-alert>

                        <v-alert v-else-if="queueTargetMode === 'same-as-last'" type="warning" variant="tonal" density="compact" class="mt-3">
                            {{ t('queues.no_last_device') }}
                        </v-alert>

                        <v-alert
                            v-else-if="queueTargetMode === 'any-compatible' && resolvedDeviceId"
                            type="info"
                            variant="tonal"
                            density="compact"
                            class="mt-3"
                        >
                            {{ t('queues.any_selected_label') }}: ID {{ resolvedDeviceId }}
                        </v-alert>

                        <v-select
                            v-if="queueTargetMode === 'pick-device'"
                            v-model="manualDeviceId"
                            :items="queueCandidateDevices"
                            item-title="name"
                            item-value="id"
                            :label="t('queues.pick_device_label')"
                            variant="outlined"
                            density="comfortable"
                            class="mt-3"
                        />
                    </v-card-text>
                </v-card>
            </div>

            <div class="queue-action">
                <v-btn
                    v-if="selectableExperiments.length > 0"
                    color="info"
                    prepend-icon="mdi-plus"
                    @click="addToQueue"
                    :disabled="formData.id === null || resolvedDeviceId === null"
                >
                    {{ t('queues.add_to_queue') }}
                </v-btn>
            </div>
        </v-card-text>
    </v-card>
</template>

<style scoped>
.queue-card {
    width: 100%;
    margin: 0 auto;
}

.queue-card__body {
    padding-top: 20px;
}

.queue-layout {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.queue-target-card {
    width: 100%;
}

.queue-field {
    min-width: 0;
}

.queue-action {
    margin-top: 16px;
}

@media (max-width: 960px) {
    .queue-action :deep(.v-btn) {
        width: 100%;
    }
}
</style>
