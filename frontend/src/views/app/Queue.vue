<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import ExperimentSelector from '@/components/experiments/ExperimentSelector.vue';
import { useI18n } from 'vue-i18n';
import { Command } from '@/types/api';
import type { ExperimentFormData } from '@/types/forms';
import { useExperiments } from '@/composables/useExperiments';
import { useExperimentLogs } from '@/composables/useExperimentLogs';
import { useQueueTarget } from '@/composables/useQueueTarget';
import { useAuthStore } from '@/stores/auth';
import { useToastStore } from '@/stores/toast';

const { t } = useI18n();
const toast = useToastStore();
const authStore = useAuthStore();
const { experiments, loading, queueSelectedExperiment, fetchExperiments } = useExperiments();
const { fetchLastUsedDeviceId } = useExperimentLogs();

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

const selectableExperiments = computed(() => experiments.value.filter((e) => !e.deleted_at && (e.devices?.length ?? 0) > 0));

const selectedExperiment = computed(() => selectableExperiments.value.find((e) => e.id === formData.value.id) ?? null);

const lastUsedDeviceId = ref<number | null>(null);

const { queueTargetMode, manualDeviceId, resolvedDeviceId, compatibleDevices } = useQueueTarget(selectedExperiment, lastUsedDeviceId);

watch(
    () => selectedExperiment.value?.id ?? null,
    async (experimentId) => {
        lastUsedDeviceId.value = null;
        if (!experimentId) return;
        lastUsedDeviceId.value = await fetchLastUsedDeviceId(experimentId);
    },
);

onMounted(async () => {
    const experimentsResult = await fetchExperiments();
    if (!experimentsResult.success) toast.error(experimentsResult.message || 'Failed to fetch available experiments');
});

const addToQueue = async () => {
    const result = await queueSelectedExperiment({
        ...formData.value,
        device_id: resolvedDeviceId.value,
        output_arguments: selectedExperiment.value?.output_arguments ?? [],
    });
    result.success ? toast.success(result.message ?? 'queued') : toast.error(result.message ?? 'failed');
};
</script>

<template>
    <v-card elevation="4">
        <v-card-title class="bg-card-title">
            <v-icon icon="mdi-clock-outline" class="mr-2" />
            <span>{{ $t('nav.queue_experiments') }}</span>
        </v-card-title>
        <v-card-text class="pt-5">
            <ExperimentSelector
                fixed-command="start"
                :loading="loading"
                :experiments="selectableExperiments"
                :selected-device-id="resolvedDeviceId"
                compact
                class="queue-field"
                @update:formData="formData = $event"
            />

            <v-radio-group v-model="queueTargetMode" hide-details>
                <v-radio :label="t('queues.target_any')" value="any-compatible" :disabled="compatibleDevices.length === 0" />
                <v-radio :label="t('queues.target_same_last')" value="same-as-last" :disabled="!lastUsedDeviceId" />
                <v-radio :label="t('queues.target_manual')" value="pick-device" :disabled="compatibleDevices.length === 0" />
            </v-radio-group>

            <v-select
                v-if="queueTargetMode === 'pick-device'"
                v-model="manualDeviceId"
                :items="compatibleDevices"
                item-title="name"
                item-value="id"
                :label="t('queues.pick_device_label')"
                variant="outlined"
                density="comfortable"
                class="mt-3"
            />
        </v-card-text>
        <v-card-actions class="queue-action" v-if="selectableExperiments.length > 0">
            <v-btn
                color="info"
                variant="elevated"
                prepend-icon="mdi-plus"
                :disabled="formData.id === null || (queueTargetMode === 'pick-device' && !manualDeviceId)"
                @click="addToQueue"
            >
                {{ t('queues.add_to_queue') }}
            </v-btn>
        </v-card-actions>
    </v-card>
</template>

<style scoped>
@media (max-width: 960px) {
    .queue-action :deep(.v-btn) {
        width: 100%;
    }
}
</style>
