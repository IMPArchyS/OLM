<script setup lang="ts">
import type { Command, Experiment, InputArgSpec, Step } from '@/types/api';
import type { QueueFormData } from '@/types/forms';
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

interface Props {
    loading: boolean;
    fixedCommand: string;
    experiments: Experiment[];
}

const props = defineProps<Props>();

const emit = defineEmits<{
    'update:formData': [data: QueueFormData];
}>();

const selectedExperimentId = ref<number | null>(null);
const simTime = ref<number>(1);
const sampleRate = ref<number>(1);
const selectedCommand = ref<Command | null>(null);
const useSetpoints = ref<boolean>(false);
const setpointStartValue = ref<number>(0);
const setpointSteps = ref<Step[]>([]);
const inputArguments = ref<Record<string, InputArgSpec>>({});

const selectedExperiment = computed(() => {
    return props.experiments.find((exp) => exp.id === selectedExperimentId.value) || null;
});

watch(
    () => props.experiments,
    (experiments) => {
        if (experiments.length === 0) {
            selectedExperimentId.value = null;
            return;
        }

        const hasSelected = experiments.some((exp) => exp.id === selectedExperimentId.value);
        if (!hasSelected) {
            const firstExperiment = experiments[0];
            selectedExperimentId.value = firstExperiment ? firstExperiment.id : null;
        }
    },
    { immediate: true },
);

watch(
    [selectedExperiment, () => props.fixedCommand],
    ([experiment, fixedCommand]) => {
        if (!experiment) {
            selectedCommand.value = null;
            return;
        }

        if (fixedCommand) {
            const fixed = experiment.commands.find((cmd) => cmd === fixedCommand) ?? null;
            selectedCommand.value = fixed;
            return;
        }

        const hasCurrent = selectedCommand.value ? experiment.commands.includes(selectedCommand.value) : false;
        if (!hasCurrent) {
            selectedCommand.value = experiment.commands.find((cmd) => cmd === 'start') ?? experiment.commands[0] ?? null;
        }
    },
    { immediate: true },
);

watch(
    selectedExperiment,
    (experiment) => {
        if (!experiment) {
            inputArguments.value = {};
            useSetpoints.value = false;
            setpointStartValue.value = 0;
            setpointSteps.value = [];
            return;
        }
        inputArguments.value = Object.fromEntries(Object.entries(experiment.input_arguments).map(([key, spec]) => [key, { ...spec }]));
        useSetpoints.value = false;
        setpointStartValue.value = 0;
        setpointSteps.value = [];
    },
    { immediate: true },
);

watch(
    useSetpoints,
    (enabled) => {
        if (!enabled) {
            setpointStartValue.value = 0;
            setpointSteps.value = [];
            return;
        }

        if (setpointSteps.value.length === 0) {
            setpointSteps.value = [
                {
                    duration: 0,
                    value: 0,
                },
            ];
        }
    },
    { immediate: true },
);

const canAddSetpointStep = computed(() => {
    return !!selectedExperiment.value && useSetpoints.value;
});

const addSetpointStep = () => {
    if (!canAddSetpointStep.value) {
        return;
    }

    setpointSteps.value.push({
        duration: 0,
        value: 0,
    });
};

const removeSetpointStep = (index: number) => {
    if (setpointSteps.value.length <= 1) {
        return;
    }

    setpointSteps.value.splice(index, 1);
};

const selectedSetpointChanges = computed<QueueFormData['setpoint_changes']>(() => {
    if (!useSetpoints.value || setpointSteps.value.length === 0) {
        return {} as Record<string, never>;
    }

    return {
        start_value: setpointStartValue.value,
        steps: setpointSteps.value,
    };
});

const experimentTitle = (e: Experiment) => `Experiment Id: ${e.id}  - ${e.server.name} | ${e.device.name} | ${e.software.name}`;

const formData = computed<QueueFormData>(() => {
    return {
        experiment_id: selectedExperimentId.value,
        command: selectedCommand.value,
        input_arguments: inputArguments.value,
        setpoint_changes: selectedSetpointChanges.value,
        device_id: selectedExperiment.value?.device.id ?? null,
        software_name: selectedExperiment.value?.software.name ?? null,
        simulation_time: simTime.value,
        sampling_rate: sampleRate.value,
    };
});

watch(
    formData,
    (newData) => {
        emit('update:formData', newData);
    },
    { deep: true },
);

defineExpose({
    formData,
});
</script>

<template>
    <div>
        <div v-if="props.loading" style="display: flex; justify-content: center; padding: 16px">
            <v-progress-circular indeterminate color="primary" size="48" />
        </div>

        <div v-else-if="props.experiments.length > 0" style="display: flex; flex-direction: column; gap: 16px">
            <v-select
                v-model="selectedExperimentId"
                :items="experiments"
                :item-title="experimentTitle"
                item-value="id"
                :label="t('dashboard.select_experiment')"
                variant="outlined"
                density="comfortable"
            />

            <v-select
                v-if="selectedExperiment?.schema_id"
                :items="[]"
                :label="t('dashboard.select_schema')"
                :placeholder="t('dashboard.no_schemas_available')"
                variant="outlined"
                density="comfortable"
            />

            <v-select
                v-if="selectedExperiment?.commands"
                v-model="selectedCommand"
                :items="selectedExperiment?.commands"
                :label="t('dashboard.select_command')"
                :placeholder="t('dashboard.no_commands_available')"
                :disabled="!!fixedCommand"
                :readonly="!!fixedCommand"
                variant="outlined"
                density="comfortable"
            />

            <v-checkbox v-if="selectedExperiment" v-model="useSetpoints" :label="t('dashboard.enable_setpoints')" density="comfortable" />

            <v-number-input
                v-if="selectedExperiment && useSetpoints"
                v-model="setpointStartValue"
                :label="t('dashboard.setpoint_start_value')"
                variant="outlined"
                density="comfortable"
            />

            <div v-if="useSetpoints && setpointSteps.length > 0" style="display: flex; flex-direction: column; gap: 12px; align-items: center">
                <div
                    v-for="(step, index) in setpointSteps"
                    :key="`setpoint-step-${index}`"
                    style="display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; width: 100%"
                >
                    <v-number-input
                        :model-value="step.duration"
                        @update:model-value="(value) => (step.duration = Number(value ?? 0))"
                        :label="`${t('dashboard.setpoint_step_duration')} #${index + 1}`"
                        :min="0"
                        variant="outlined"
                        density="comfortable"
                        style="max-width: 220px"
                    />
                    <v-number-input
                        :model-value="step.value"
                        @update:model-value="(value) => (step.value = Number(value ?? 0))"
                        :label="`${t('dashboard.setpoint_step_value')} #${index + 1}`"
                        variant="outlined"
                        density="comfortable"
                        style="max-width: 220px"
                    />
                    <v-btn color="error" variant="text" icon="mdi-delete" :disabled="setpointSteps.length <= 1" @click="removeSetpointStep(index)" />
                </div>
            </div>

            <div v-if="selectedExperiment && useSetpoints" style="display: flex; flex-direction: column; gap: 8px; align-items: center">
                <v-btn :disabled="!canAddSetpointStep" color="info" variant="tonal" prepend-icon="mdi-plus" @click="addSetpointStep">
                    {{ t('dashboard.add_setpoint_step') }}
                </v-btn>
            </div>

            <!-- Experiment Command Parameters  " -->
            <div v-if="Object.keys(inputArguments).length > 0">
                <div v-for="(spec, key) in inputArguments" :key="key" style="margin-bottom: 12px">
                    <v-text-field
                        v-if="spec.type === 'string'"
                        :label="spec.unit ? `${t('experiment_input_arg.' + key)} (${spec.unit})` : t('experiment_input_arg.' + key)"
                        v-model="spec.value"
                        variant="outlined"
                        density="comfortable"
                    />
                    <v-number-input
                        v-else-if="spec.type === 'number'"
                        :label="spec.unit ? `${t('experiment_input_arg.' + key)} (${spec.unit})` : t('experiment_input_arg.' + key)"
                        :model-value="Number(spec.value)"
                        @update:model-value="(value) => (spec.value = Number(value ?? 0))"
                        variant="outlined"
                        density="comfortable"
                    />
                </div>
            </div>

            <v-number-input
                v-if="selectedExperiment"
                v-model="simTime"
                :label="t('dashboard.simulation_time')"
                :min="1"
                variant="outlined"
                density="comfortable"
            />
            <v-number-input
                v-if="selectedExperiment"
                v-model="sampleRate"
                :label="t('dashboard.sampling_rate')"
                :min="1"
                variant="outlined"
                density="comfortable"
            />

            <!-- Slot for additional controls (e.g., buttons) -->
            <slot
                :selected-experiment="selectedExperiment"
                :selected-command="selectedCommand"
                :experiment-input-args-values="inputArguments"
                :sim-time="simTime"
                :sample-rate="sampleRate"
            />
        </div>

        <!-- Empty State -->
        <v-alert v-else type="error" variant="tonal">
            {{ t('queues.no_experiment_found') }}
        </v-alert>
    </div>
</template>
