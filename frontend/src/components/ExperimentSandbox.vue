<script setup lang="ts">
import { ref, watch, computed } from 'vue'

interface Reservation {
    id: number
    start: string
    end: string
    device_id: number
    username?: string
}

interface Experiment {
    id: number
    name: string
    description?: string
    device_id: number
    has_schema?: boolean
    commands?: Record<string, string> // Object with key-value pairs like {"start": "begin_monitoring"}
    experiment_commands?: Record<string, string> // Object with key-value pairs like {"calibrate": "calibrate_sensor"}
}

interface ExperimentCommandValues {
    [key: string]: string | number
}

const props = defineProps<{ reservation: Reservation }>()

const experiments = ref<Experiment[]>([])
const selectedExperimentId = ref<number | null>(null)
const selectedCommand = ref<string>('')
const experimentCommandValues = ref<ExperimentCommandValues>({})
const loading = ref(false)
const error = ref<string | null>(null)

const selectedExperiment = computed(() => {
    return experiments.value.find((exp) => exp.id === selectedExperimentId.value) || null
})

const commandEntries = computed(() => {
    if (!selectedExperiment.value?.commands) return []
    return Object.entries(selectedExperiment.value.commands)
})

const experimentCommandEntries = computed(() => {
    if (!selectedExperiment.value?.experiment_commands) return []
    return Object.entries(selectedExperiment.value.experiment_commands)
})

const initializeExperimentCommandValues = (experiment: Experiment) => {
    if (!experiment.experiment_commands) return

    const values: ExperimentCommandValues = {}
    Object.entries(experiment.experiment_commands).forEach(([key, value]) => {
        values[key] = value
    })
    experimentCommandValues.value = values
}

const fetchExperiments = async (deviceId: number) => {
    loading.value = true
    error.value = null

    try {
        const response = await fetch(`http://localhost:8000/api/experiment/?device_id=${deviceId}`)

        if (response.ok) {
            const data = await response.json()
            // Set experiment name to "exp-id-" + id
            experiments.value = data.map((exp: Experiment) => ({
                ...exp,
                name: `exp-id-${exp.id}`,
            }))

            if (experiments.value.length === 0) {
                error.value = 'No experiments found for this device'
            } else if (experiments.value[0]) {
                // Auto-select the first experiment
                selectedExperimentId.value = experiments.value[0].id
                initializeExperimentCommandValues(experiments.value[0])
                // Auto-select first command if available
                if (experiments.value[0].commands) {
                    const commandKeys = Object.keys(experiments.value[0].commands)
                    if (commandKeys.length > 0) {
                        selectedCommand.value = commandKeys[0] ?? ''
                    }
                }
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
        initializeExperimentCommandValues(newExperiment)
        // Auto-select first command
        if (newExperiment.commands) {
            const commandKeys = Object.keys(newExperiment.commands)
            if (commandKeys.length > 0) {
                selectedCommand.value = commandKeys[0] ?? ''
            }
        }
    }
})
console.log(experiments)
</script>

<template>
    <v-card class="mt-4">
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
                    disabled
                />

                <!-- Experiment Parameters Section (from experiment_commands) -->
                <v-card v-if="experimentCommandEntries.length > 0" variant="tonal">
                    <v-card-text>
                        <h4 class="text-lg font-weight-medium mb-4">
                            {{ $t('dashboard.experiment_parameters') }}
                        </h4>

                        <v-row>
                            <v-col
                                v-for="[key, value] in experimentCommandEntries"
                                :key="key"
                                cols="12"
                                md="6"
                            >
                                <v-text-field
                                    v-model="experimentCommandValues[key]"
                                    :label="key"
                                    :placeholder="key"
                                    variant="outlined"
                                    density="comfortable"
                                />
                            </v-col>
                        </v-row>

                        <div style="display: flex; justify-content: flex-end; margin-top: 16px">
                            <v-btn color="primary" variant="elevated">
                                {{ $t('dashboard.run_experiment') }}
                            </v-btn>
                        </div>
                    </v-card-text>
                </v-card>

                <!-- Command Selector -->
                <v-select
                    v-if="commandEntries.length > 0"
                    v-model="selectedCommand"
                    :items="
                        commandEntries.map(([key, value]) => ({
                            title: `${key} - ${value}`,
                            value: key,
                        }))
                    "
                    :label="$t('dashboard.select_command')"
                    variant="outlined"
                    density="comfortable"
                />

                <!-- Selected Experiment Details -->
                <v-card v-if="selectedExperiment" variant="tonal">
                    <v-card-text>
                        <h4 class="text-lg font-weight-medium">{{ selectedExperiment.name }}</h4>
                        <p v-if="selectedExperiment.description" class="text-sm mt-2">
                            {{ selectedExperiment.description }}
                        </p>
                        <v-divider class="my-2" />
                        <pre
                            class="text-xs pa-3 rounded"
                            style="background-color: rgba(0, 0, 0, 0.05); overflow: auto"
                            >{{ selectedExperiment }}</pre
                        >
                    </v-card-text>
                </v-card>
            </div>

            <v-alert v-else type="warning" variant="tonal">
                {{ $t('dashboard.no_experiment_found') }}
            </v-alert>
        </v-card-text>
    </v-card>
</template>
