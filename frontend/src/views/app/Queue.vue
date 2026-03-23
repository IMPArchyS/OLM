<script setup lang="ts">
import { onMounted, ref } from 'vue';
import ExperimentSelector from '@/components/ExperimentSelector.vue';
import { useI18n } from 'vue-i18n';
import { Command } from '@/types/api';
import type { QueueFormData } from '@/types/forms';
import { useExperiments } from '@/composables/useExperiments';
import { useToast } from '@/composables/useToast';

const { t } = useI18n();
const { showError } = useToast();
const { experiments, loading, error, fetchExperiments } = useExperiments();

const formData = ref<QueueFormData>({
    experiment_id: null,
    command: Command.START,
    input_arguments: {},
    setpoint_changes: {},
    device_id: null,
    software_name: null,
    simulation_time: 0,
    sampling_rate: 0,
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
    console.log(JSON.stringify(formData.value, null, 2));
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
                :disabled="formData.experiment_id === null"
            >
                {{ t('queues.add_to_queue') }}
            </v-btn>
        </v-card-text>
    </v-card>
</template>
