<script setup lang="ts">
import { onMounted, ref } from 'vue';
import ExperimentSelector from '@/components/ExperimentSelector.vue';
import { useI18n } from 'vue-i18n';
import { Command } from '@/types/api';
import type { QueueFormData } from '@/types/forms';
import { useExperiments } from '@/composables/useExperiments';
import { useToast } from '@/composables/useToast';
import { useAuthStore } from '@/stores/auth';

const { t } = useI18n();
const { showError, showInfo } = useToast();
const authStore = useAuthStore();
const { experiments, loading, error, fetchExperiments, queueSelectedExperiment } = useExperiments();

const formData = ref<QueueFormData>({
    user_id: authStore.user?.id ?? null,
    id: null,
    server_id: null,
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
    const result = await fetchExperiments();
    if (!result.success) {
        showError(result.message || 'Failed');
    }
});

const handleFormDataUpdate = (data: typeof formData.value) => {
    formData.value = data;
};

const addToQueue = async () => {
    const selectedExperiment = experiments.value.find((exp) => exp.id === formData.value.id);
    formData.value.output_arguments = selectedExperiment?.output_arguments ?? [];

    console.log(JSON.stringify(formData.value, null, 2));
    const result = await queueSelectedExperiment(formData.value);
    if (!result.success) {
        showError(result.message || 'Failed');
    } else {
        showInfo(result.message || 'Queued');
    }
};
</script>

<template>
    <v-card class="mt-5">
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ t('queues.title') }}</span>
        </v-card-title>
        <v-card-text class="mt-5">
            <ExperimentSelector fixed-command="start" :loading="loading" :experiments="experiments" @update:formData="handleFormDataUpdate" />
            <v-btn
                v-if="experiments.length > 0"
                color="info"
                prepend-icon="mdi-plus"
                @click="addToQueue"
                class="mt-4"
                :disabled="formData.id === null"
            >
                {{ t('queues.add_to_queue') }}
            </v-btn>
        </v-card-text>
    </v-card>
</template>
