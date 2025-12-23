<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import type { Experiment, CommandSpec } from '@/types/api';
import { apiClient } from '@/composables/useAxios';

interface Props {
    deviceId?: number | null;
    fixedCommand?: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
    'update:formData': [
        data: {
            experiment_id: number | null;
            command: string;
            experiment_commands: Record<string, any>;
            simulation_time: number;
            sampling_rate: number;
        },
    ];
}>();

const experiments = ref<Experiment[]>([]);
const selectedExperimentId = ref<number | null>(null);
const selectedCommand = ref<string>('');
const loading = ref(false);
const error = ref<string | null>(null);
const experimentCommandValues = ref<Record<string, any>>({});
const simTime = ref<number>(0);
const sampleRate = ref<number>(0);

const selectedExperiment = computed(() => {
    return experiments.value.find((exp) => exp.id === selectedExperimentId.value) || null;
});

function convertCommandsToSpecs(
    commands: Record<string, { cmd: string }>,
): Record<string, CommandSpec> {
    return Object.fromEntries(
        Object.entries(commands).map(([key, val]) => [key, { type: 'string', value: val.cmd }]),
    );
}

const fetchExperiments = async (deviceId?: number | null) => {
    loading.value = true;
    error.value = null;

    try {
        const url = deviceId ? `/experiment/device/${deviceId}` : '/experiment/';
        const response = await apiClient.get(url);
        const data = response.data;

        const experimentsWithNames = await Promise.all(
            data.map(async (exp: any) => {
                let experimentName = exp.name;

                if (!experimentName) {
                    let deviceName = 'device';
                    let softwareName = 'software';

                    if (exp.device_id) {
                        try {
                            const deviceResponse = await apiClient.get(`/device/${exp.device_id}`);
                            deviceName = deviceResponse.data.name || deviceName;
                        } catch (e) {
                            console.error(`Error fetching device ${exp.device_id}:`, e);
                        }
                    }

                    if (exp.software_id) {
                        try {
                            const softwareResponse = await apiClient.get(
                                `/software/${exp.software_id}`,
                            );
                            softwareName = softwareResponse.data.name || softwareName;
                        } catch (e) {
                            console.error(`Error fetching software ${exp.software_id}:`, e);
                        }
                    }

                    experimentName = `${deviceName} - ${softwareName}`;
                }

                return {
                    id: exp.id,
                    name: experimentName,
                    description: exp.description,
                    device_id: exp.device_id,
                    has_schema: exp.has_schema,
                    commands: exp.commands ? convertCommandsToSpecs(exp.commands) : undefined,
                    experiment_commands: exp.experiment_commands
                        ? Object.fromEntries(
                              Object.entries(exp.experiment_commands).map(([key, val]) => [
                                  key,
                                  val,
                              ]),
                          )
                        : undefined,
                };
            }),
        );

        experiments.value = experimentsWithNames;

        if (experiments.value.length === 0) {
            error.value = deviceId
                ? 'No experiments found for this device'
                : 'No experiments available';
        } else {
            selectedExperimentId.value = experiments.value[0]?.id ?? null;
        }
    } catch (e) {
        console.error('Error fetching experiments:', e);
        error.value = 'Error fetching experiments';
        experiments.value = [];
    } finally {
        loading.value = false;
    }
};

// Watch for deviceId changes and fetch experiments
watch(
    () => props.deviceId,
    (newDeviceId) => {
        // Always fetch: with deviceId if provided, or all experiments if not
        fetchExperiments(newDeviceId);
    },
    { immediate: true },
);

// Watch for experiment selection changes and reinitialize command values
watch(selectedExperiment, (newExperiment) => {
    if (newExperiment) {
        // Set default values for experiment commands
        if (newExperiment?.experiment_commands) {
            experimentCommandValues.value = Object.fromEntries(
                Object.entries(newExperiment.experiment_commands).map(([key, spec]) => [
                    key,
                    spec.value ?? (spec.type === 'number' ? 0 : ''),
                ]),
            );
        }
        // Set command: use fixedCommand if provided, otherwise use first available command
        if (props.fixedCommand) {
            selectedCommand.value = props.fixedCommand;
        } else if (newExperiment?.commands) {
            const commandKeys = Object.keys(newExperiment.commands);
            if (commandKeys.length > 0) {
                selectedCommand.value = commandKeys[0] ?? '';
            }
        }
    }
});

const formData = computed(() => {
    const parameters: Record<string, CommandSpec> = {};

    if (selectedExperiment.value?.experiment_commands) {
        Object.entries(experimentCommandValues.value).forEach(([key, value]) => {
            const originalSpec = selectedExperiment.value?.experiment_commands?.[key];
            if (originalSpec) {
                parameters[key] = {
                    value: value,
                    type: originalSpec.type,
                    unit: originalSpec.unit ?? null,
                };
            }
        });
    }

    return {
        experiment_id: selectedExperimentId.value,
        command: selectedCommand.value,
        experiment_commands: parameters,
        simulation_time: simTime.value,
        sampling_rate: sampleRate.value,
    };
});

// Emit form data changes
watch(
    formData,
    (newData) => {
        emit('update:formData', newData);
    },
    { deep: true },
);

// Expose data for parent component
defineExpose({
    selectedExperiment,
    selectedCommand,
    experimentCommandValues,
    simTime,
    sampleRate,
    formData,
});
</script>

<template>
    <div>
        <!-- Loading State -->
        <div v-if="loading" style="display: flex; justify-content: center; padding: 16px">
            <v-progress-circular indeterminate color="primary" size="48" />
        </div>

        <!-- Error State -->
        <v-alert v-else-if="error" type="error" variant="tonal">
            {{ error }}
        </v-alert>

        <!-- Experiment Form -->
        <div
            v-else-if="experiments.length > 0"
            style="display: flex; flex-direction: column; gap: 16px"
        >
            <!-- Experiment Selector -->
            <v-select
                v-model="selectedExperimentId"
                :items="experiments"
                item-title="name"
                item-value="id"
                :label="$t('dashboard.select_experiment')"
                variant="outlined"
                density="comfortable"
            />

            <!-- Schema Selector (only if experiment has schema) -->
            <v-select
                v-if="selectedExperiment?.has_schema"
                :items="[]"
                :label="$t('dashboard.select_schema')"
                :placeholder="$t('dashboard.no_schemas_available')"
                variant="outlined"
                density="comfortable"
            />

            <!-- Command Selector (disabled if using fixed command) -->
            <v-select
                v-if="selectedExperiment?.commands"
                v-model="selectedCommand"
                :items="Object.keys(selectedExperiment.commands)"
                :label="$t('dashboard.select_command')"
                :placeholder="$t('dashboard.no_commands_available')"
                :disabled="!!fixedCommand"
                :readonly="!!fixedCommand"
                variant="outlined"
                density="comfortable"
            />

            <!-- Experiment Command Parameters -->
            <div v-if="selectedExperiment?.experiment_commands">
                <div
                    v-for="(spec, key) in selectedExperiment.experiment_commands"
                    :key="key"
                    style="margin-bottom: 12px"
                >
                    <v-text-field
                        v-if="spec.type === 'string'"
                        :label="
                            spec.unit
                                ? `${$t('experiment_command.' + key)} (${spec.unit})`
                                : $t('experiment_command.' + key)
                        "
                        v-model="experimentCommandValues[key]"
                        variant="outlined"
                        density="comfortable"
                    />
                    <v-number-input
                        v-else-if="spec.type === 'number'"
                        :label="
                            spec.unit
                                ? `${$t('experiment_command.' + key)} (${spec.unit})`
                                : $t('experiment_command.' + key)
                        "
                        v-model="experimentCommandValues[key]"
                        :min="0"
                        variant="outlined"
                        density="comfortable"
                    />
                </div>
            </div>

            <!-- Universal Simulation Parameters -->
            <v-number-input
                v-model="simTime"
                :label="$t('dashboard.simulation_time')"
                :min="0"
                variant="outlined"
                density="comfortable"
            />
            <v-number-input
                v-model="sampleRate"
                :label="$t('dashboard.sampling_rate')"
                :min="0"
                variant="outlined"
                density="comfortable"
            />

            <!-- Slot for additional controls (e.g., buttons) -->
            <slot
                :selected-experiment="selectedExperiment"
                :selected-command="selectedCommand"
                :experiment-command-values="experimentCommandValues"
                :sim-time="simTime"
                :sample-rate="sampleRate"
            />
        </div>

        <!-- Empty State -->
        <v-alert v-else type="warning" variant="tonal">
            {{ $t('dashboard.no_experiment_found') }}
        </v-alert>
    </div>
</template>
