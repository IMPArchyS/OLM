<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { CommandSpec, Experiment, Reservation } from '@/types/api'

// Converts backend commands object to CommandSpec format
function convertCommandsToSpecs(
    commands: Record<string, { cmd: string }>,
): Record<string, CommandSpec> {
    return Object.fromEntries(
        Object.entries(commands).map(([key, val]) => [key, { type: 'string', value: val.cmd }]),
    )
}

const props = defineProps<{ reservation: Reservation }>()

const experiments = ref<Experiment[]>([])
const selectedExperimentId = ref<number | null>(null)
const selectedCommand = ref<string>('')
const loading = ref(false)
const error = ref<string | null>(null)
const experimentCommandValues = ref<Record<string, any>>({})

function runExperiment() {
    if (!selectedExperiment.value) {
        console.error('No experiment selected')
        return
    }
    const missing = Object.entries(selectedExperiment.value.experiment_commands || {})
        .filter(
            ([key, spec]) =>
                experimentCommandValues.value[key] === undefined ||
                experimentCommandValues.value[key] === null ||
                experimentCommandValues.value[key] === '',
        )
        .map(([key]) => key)
    if (missing.length > 0) {
        alert('Please fill in all experiment command values: ' + missing.join(', '))
        return
    }
    const payload = {
        experiment_id: selectedExperiment.value.id,
        command: selectedCommand.value,
        values: { ...experimentCommandValues.value },
    }
    console.log('Payload to send:', JSON.stringify(payload, null, 2))
}

const selectedExperiment = computed(() => {
    return experiments.value.find((exp) => exp.id === selectedExperimentId.value) || null
})

const fetchExperiments = async (deviceId: number) => {
    loading.value = true
    error.value = null

    try {
        const response = await fetch(`http://localhost:8000/api/experiment/?device_id=${deviceId}`)

        if (response.ok) {
            const data = await response.json()
            // Set experiment name to "exp-id-" + id
            experiments.value = data.map((exp: any) => ({
                id: exp.id,
                name: `exp-id-${exp.id}`,
                description: exp.description,
                device_id: exp.device_id,
                has_schema: exp.has_schema,
                commands: exp.commands ? convertCommandsToSpecs(exp.commands) : undefined,
                experiment_commands: exp.experiment_commands
                    ? Object.fromEntries(
                          Object.entries(exp.experiment_commands).map(([key, val]) => [key, val]),
                      )
                    : undefined,
            }))
            console.log('Fetched experiments:', JSON.stringify(experiments.value, null, 2))

            if (experiments.value.length === 0) {
                error.value = 'No experiments found for this device'
            } else if (experiments.value[0]) {
                // Auto-select the first experiment
                selectedExperimentId.value = experiments.value[0].id
                // Auto-select first command if available
            }
        } else {
            error.value = `Failed to fetch experiments: ${response.statusText}`
            experiments.value = []
        }
    } catch (e) {
        console.error('Error fetching experiments:', e)
        error.value = 'Error fetching experiments'
        experiments.value = []
    } finally {
        loading.value = false
    }
}

// Fetch experiments when component mounts or when device_id changes
watch(
    () => props.reservation.device_id,
    (newDeviceId) => {
        if (newDeviceId) {
            fetchExperiments(newDeviceId)
        }
    },
    { immediate: true },
)

// Watch for experiment selection changes and reinitialize command values
watch(selectedExperiment, (newExperiment) => {
    if (newExperiment) {
        // Set default values for experiment commands
        if (newExperiment?.experiment_commands) {
            experimentCommandValues.value = Object.fromEntries(
                Object.entries(newExperiment.experiment_commands).map(([key, spec]) => [
                    key,
                    spec.value,
                ]),
            )
        }
        // Set first command as default
        if (newExperiment?.commands) {
            const commandKeys = Object.keys(newExperiment.commands)
            if (commandKeys.length > 0) {
                selectedCommand.value = commandKeys[0] ?? ''
            }
        }
    }
})
</script>

<template>
    <v-card class="mt-4 overflow-auto!" style="height: calc(100vh - 260px)">
        <v-card-title>{{ $t('dashboard.ongoing_experiment') }}</v-card-title>

        <v-card-text>
            <div v-if="loading" style="display: flex; justify-content: center; padding: 16px">
                <v-progress-circular indeterminate color="primary" size="48" />
            </div>

            <v-alert v-else-if="error" type="error" variant="tonal">
                {{ error }}
            </v-alert>

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
                <v-select
                    v-if="selectedExperiment?.commands"
                    v-model="selectedCommand"
                    :items="Object.keys(selectedExperiment.commands)"
                    :label="$t('dashboard.select_command')"
                    :placeholder="$t('dashboard.no_commands_available')"
                    variant="outlined"
                    density="comfortable"
                />
                <div v-if="selectedExperiment?.experiment_commands">
                    <div
                        v-for="(spec, key) in selectedExperiment.experiment_commands"
                        :key="key"
                        style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px"
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
                <v-number-input
                    :label="$t('dashboard.sim_time')"
                    :min="0"
                    variant="outlined"
                    density="comfortable"
                />
                <v-number-input
                    :label="$t('dashboard.sample_rate')"
                    :min="0"
                    variant="outlined"
                    density="comfortable"
                />
                <v-btn color="primary" variant="elevated" @click="runExperiment">
                    {{ $t('dashboard.run_experiment') }}
                </v-btn>
            </div>

            <v-alert v-else type="warning" variant="tonal">
                {{ $t('dashboard.no_experiment_found') }}
            </v-alert>
        </v-card-text>
    </v-card>
</template>
