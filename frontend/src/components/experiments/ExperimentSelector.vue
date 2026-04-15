<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import type { Command, Experiment, InputArgSpec, Step } from '@/types/api';
import type { QueueFormData } from '@/types/forms';
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const authStore = useAuthStore();

interface Props {
    loading: boolean;
    fixedCommand: string;
    experiments: Experiment[];
    selectedDeviceId?: number | null;
    compact?: boolean;
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

const inputDensity = computed(() => {
    return props.compact ? 'compact' : 'comfortable';
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

const experimentPrimaryDevice = (e: Experiment | null) => {
    if (!e) {
        return null;
    }

    const selectedDevice = e.devices?.find((device) => device.id === props.selectedDeviceId);
    return selectedDevice ?? e.devices?.[0] ?? null;
};

const experimentTitle = (e: Experiment) => {
    const primaryDevice = experimentPrimaryDevice(e);
    const deviceName = primaryDevice ? primaryDevice.name : 'No device';
    return `Experiment Id: ${e.id} - ${deviceName} | ${e.software.name}`;
};

const inputLabel = (key: string, spec: InputArgSpec) => {
    const label = t('experiment_input_arg.' + key);
    return spec.unit ? `${label} (${spec.unit})` : label;
};

const inputGridMinWidthCh = computed(() => {
    const baseLabels = [t('dashboard.simulation_time'), t('dashboard.sampling_rate')];
    const dynamicLabels = Object.entries(inputArguments.value).map(([key, spec]) => inputLabel(key, spec));
    const allLabels = [...baseLabels, ...dynamicLabels];
    const longestLabelLength = allLabels.reduce((max, label) => Math.max(max, label.length), 0);

    return Math.max(20, longestLabelLength + 4);
});

const inputGridStyle = computed(() => {
    return {
        '--experiment-grid-min-ch': String(inputGridMinWidthCh.value),
    };
});

const formData = computed<QueueFormData>(() => {
    return {
        user_id: authStore.user?.id ?? null,
        id: selectedExperimentId.value,
        command: selectedCommand.value,
        input_arguments: inputArguments.value,
        output_arguments: selectedExperiment.value?.output_arguments ?? [],
        setpoint_changes: selectedSetpointChanges.value,
        schema_id: null,
        device_id: props.selectedDeviceId ?? experimentPrimaryDevice(selectedExperiment.value)?.id ?? null,
        software_name: selectedExperiment.value?.software.name ?? null,
        simulation_time: simTime.value,
        sample_rate: sampleRate.value,
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
    <div :class="['experiment-selector', { 'experiment-selector--compact': props.compact }]">
        <div v-if="props.loading" class="experiment-selector__loading">
            <v-progress-circular indeterminate color="primary" size="48" />
        </div>

        <div v-else-if="props.experiments.length > 0" class="experiment-selector__stack">
            <div class="experiment-selector__experiment-row">
                <v-select
                    v-model="selectedExperimentId"
                    :items="experiments"
                    :item-title="experimentTitle"
                    item-value="id"
                    :label="t('dashboard.select_experiment')"
                    variant="outlined"
                    :density="inputDensity"
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
                    :density="inputDensity"
                />
            </div>

            <v-select
                v-if="selectedExperiment?.schema_id"
                :items="[]"
                :label="t('dashboard.select_schema')"
                :placeholder="t('dashboard.no_schemas_available')"
                variant="outlined"
                :density="inputDensity"
            />

            <v-checkbox
                v-if="selectedExperiment"
                v-model="useSetpoints"
                :label="t('dashboard.enable_setpoints')"
                :density="inputDensity"
                class="experiment-selector__checkbox"
            />

            <v-number-input
                v-if="selectedExperiment && useSetpoints"
                v-model="setpointStartValue"
                :label="t('dashboard.setpoint_start_value')"
                variant="outlined"
                :density="inputDensity"
            />

            <div v-if="useSetpoints && setpointSteps.length > 0" class="experiment-selector__steps">
                <div
                    v-for="(step, index) in setpointSteps"
                    :key="`setpoint-step-${index}`"
                    class="experiment-selector__step"
                >
                    <v-number-input
                        :model-value="step.duration"
                        @update:model-value="(value) => (step.duration = Number(value ?? 0))"
                        :label="`${t('dashboard.setpoint_step_duration')} #${index + 1}`"
                        :min="0"
                        variant="outlined"
                        :density="inputDensity"
                    />
                    <v-number-input
                        :model-value="step.value"
                        @update:model-value="(value) => (step.value = Number(value ?? 0))"
                        :label="`${t('dashboard.setpoint_step_value')} #${index + 1}`"
                        variant="outlined"
                        :density="inputDensity"
                    />
                    <v-btn color="error" variant="text" icon="mdi-delete" :disabled="setpointSteps.length <= 1" @click="removeSetpointStep(index)" />
                </div>
            </div>

            <div v-if="selectedExperiment && useSetpoints" class="experiment-selector__setpoint-action">
                <v-btn :disabled="!canAddSetpointStep" color="info" variant="tonal" prepend-icon="mdi-plus" @click="addSetpointStep">
                    {{ t('dashboard.add_setpoint_step') }}
                </v-btn>
            </div>

            <!-- Experiment Command Parameters  " -->
            <div v-if="selectedExperiment" class="experiment-selector__args-grid" :style="inputGridStyle">
                <div v-for="(spec, key) in inputArguments" :key="key" class="experiment-selector__grid-cell">
                    <v-text-field
                        v-if="spec.type === 'string'"
                        :label="inputLabel(key, spec)"
                        v-model="spec.value"
                        variant="outlined"
                        :density="inputDensity"
                    />
                    <v-text-field
                        v-else-if="spec.type === 'number'"
                        :label="inputLabel(key, spec)"
                        :model-value="Number(spec.value)"
                        @update:model-value="(value) => (spec.value = Number(value ?? 0))"
                        variant="outlined"
                        :density="inputDensity"
                    />
                </div>

                <div class="experiment-selector__grid-cell">
                    <v-text-field
                        v-model="simTime"
                        :label="t('dashboard.simulation_time')"
                        variant="outlined"
                        :density="inputDensity"
                    />
                </div>

                <div class="experiment-selector__grid-cell">
                    <v-text-field
                        v-model="sampleRate"
                        :label="t('dashboard.sampling_rate')"
                        variant="outlined"
                        :density="inputDensity"
                    />
                </div>
            </div>

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
        <v-alert v-else type="info" variant="tonal">
            {{ t('queues.no_experiment_found') }}
        </v-alert>
    </div>
</template>

<style scoped>
.experiment-selector {
    width: 100%;
}

.experiment-selector__loading {
    display: flex;
    justify-content: center;
    padding: 16px;
}

.experiment-selector__stack {
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.experiment-selector__experiment-row {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.experiment-selector__checkbox {
    margin-top: -4px;
}

.experiment-selector__steps {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.experiment-selector__step {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr)) auto;
    gap: 12px;
    align-items: start;
}

.experiment-selector__setpoint-action {
    display: flex;
    justify-content: flex-start;
}

.experiment-selector__args-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, calc(var(--experiment-grid-min-ch, 24) * 1ch)), 1fr));
    gap: 12px;
}

.experiment-selector__grid-cell {
    min-width: 0;
}

.experiment-selector--compact :deep(.v-input) {
    max-width: 100%;
}

@media (max-width: 760px) {
    .experiment-selector__step {
        grid-template-columns: minmax(0, 1fr);
    }

    .experiment-selector__experiment-row {
        grid-template-columns: minmax(0, 1fr);
    }
}
</style>
