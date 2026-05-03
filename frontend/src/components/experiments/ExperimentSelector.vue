<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import type { Command, Experiment, InputArgSpec } from '@/types/api';
import type { ExperimentFormData } from '@/types/forms';
import { ref, computed, watch, watchEffect } from 'vue';
import { useI18n } from 'vue-i18n';
import { useSetpointEditor } from '@/composables/useSetpointEditor';
import SetpointEditor from './SetpointEditor.vue';

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
    'update:formData': [data: ExperimentFormData];
}>();

const selectedExperimentId = ref<number | null>(null);
const simTime = ref<number>(1);
const sampleRate = ref<number>(1);
const selectedCommand = ref<Command | null>(null);
const inputArguments = ref<Record<string, InputArgSpec>>({});

const selectedExperiment = computed(() => {
    return props.experiments.find((exp) => exp.id === selectedExperimentId.value) || null;
});

const inputDensity = computed<'compact' | 'comfortable'>(() => {
    return props.compact ? 'compact' : 'comfortable';
});

const { useSetpoints, setpointStartValue, setpointSteps, addSetpointStep, removeSetpointStep, setpointChanges } =
    useSetpointEditor(selectedExperiment);

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
        inputArguments.value = experiment
            ? Object.fromEntries(Object.entries(experiment.input_arguments).map(([key, spec]) => [key, { ...spec }]))
            : {};
    },
    { immediate: true },
);

const experimentPrimaryDevice = (e: Experiment | null) => {
    if (!e) return null;
    const selectedDevice = e.devices?.find((device) => device.id === props.selectedDeviceId);
    return selectedDevice ?? e.devices?.[0] ?? null;
};

const experimentTitle = (e: Experiment) => {
    const primaryDevice = experimentPrimaryDevice(e);
    const deviceName = primaryDevice ? primaryDevice.name : t('dashboard.no_device');
    return `Experiment Id: ${e.id} - ${deviceName} | ${e.software.name}`;
};

const inputLabel = (key: string, spec: InputArgSpec) => {
    const label = t('experiment_input_arg.' + key);
    return spec.unit ? `${label} (${spec.unit})` : label;
};

const formData = computed<ExperimentFormData>(() => {
    return {
        user_id: authStore.user?.id ?? null,
        id: selectedExperimentId.value,
        command: selectedCommand.value,
        input_arguments: inputArguments.value,
        output_arguments: selectedExperiment.value?.output_arguments ?? [],
        setpoint_changes: setpointChanges.value,
        device_id: props.selectedDeviceId ?? experimentPrimaryDevice(selectedExperiment.value)?.id ?? null,
        software_name: selectedExperiment.value?.software.name ?? null,
        simulation_time: simTime.value,
        sample_rate: sampleRate.value,
    };
});

watchEffect(() => {
    emit('update:formData', formData.value);
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

            <SetpointEditor
                v-if="selectedExperiment"
                v-model:enabled="useSetpoints"
                v-model:start-value="setpointStartValue"
                :steps="setpointSteps"
                :density="inputDensity"
                @add="addSetpointStep"
                @remove="removeSetpointStep"
                @update-step="(i, field, val) => (setpointSteps[i]![field] = val)"
            />

            <div v-if="selectedExperiment" class="experiment-selector__args-grid">
                <div v-for="(spec, key) in inputArguments" :key="key" class="experiment-selector__grid-cell">
                    <v-text-field
                        v-if="spec.type === 'string'"
                        :label="inputLabel(key, spec)"
                        v-model="spec.value"
                        variant="outlined"
                        :density="inputDensity"
                    />
                    <v-number-input
                        v-else-if="spec.type === 'number'"
                        :label="inputLabel(key, spec)"
                        :step="0.001"
                        :model-value="Number(spec.value)"
                        variant="outlined"
                        :density="inputDensity"
                        @update:model-value="(value) => (spec.value = Math.round((value ?? 0) * 1000) / 1000)"
                    />
                </div>

                <div class="experiment-selector__grid-cell">
                    <v-number-input
                        :step="0.001"
                        :min="0.001"
                        :rules="[(v: number) => v > 0 || t('dashboard.must_be_positive')]"
                        :model-value="simTime"
                        :label="t('dashboard.simulation_time')"
                        variant="outlined"
                        :density="inputDensity"
                        @update:model-value="(v) => (simTime = Math.round((v ?? 0) * 1000) / 1000)"
                    />
                </div>

                <div class="experiment-selector__grid-cell">
                    <v-number-input
                        :step="0.001"
                        :min="0.001"
                        :rules="[(v: number) => v > 0 || t('dashboard.must_be_positive')]"
                        :model-value="sampleRate"
                        :label="t('dashboard.sampling_rate')"
                        variant="outlined"
                        :density="inputDensity"
                        @update:model-value="(v) => (sampleRate = Math.round((v ?? 0) * 1000) / 1000)"
                    />
                </div>
            </div>

            <slot
                :selected-experiment="selectedExperiment"
                :selected-command="selectedCommand"
                :experiment-input-args-values="inputArguments"
                :sim-time="simTime"
                :sample-rate="sampleRate"
            />
        </div>
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

.experiment-selector__args-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.experiment-selector__args-grid > :last-child:nth-child(odd) {
    grid-column: 1 / -1;
}

.experiment-selector__grid-cell {
    min-width: 0;
}

.experiment-selector--compact :deep(.v-input) {
    max-width: 100%;
}

@media (max-width: 760px) {
    .experiment-selector__args-grid {
        grid-template-columns: minmax(0, 1fr);
    }

    .experiment-selector__experiment-row {
        grid-template-columns: minmax(0, 1fr);
    }
}
</style>
