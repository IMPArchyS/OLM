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
    <div class="card bg-base-100 shadow-xl mt-4!">
        <div class="card-body">
            <h3 class="card-title">{{ $t('dashboard.ongoing_experiment') }}</h3>

            <div v-if="loading" class="flex justify-center p-4">
                <span class="loading loading-spinner loading-md"></span>
            </div>

            <div v-else-if="error" class="alert alert-error">
                <span>{{ error }}</span>
            </div>

            <div v-else-if="experiments.length > 0" class="space-y-4">
                <!-- Experiment Selector -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">{{ $t('dashboard.select_experiment') }}</span>
                    </label>
                    <select v-model="selectedExperimentId" class="select select-bordered w-full">
                        <option v-for="exp in experiments" :key="exp.id" :value="exp.id">
                            {{ exp.name }}
                        </option>
                    </select>
                </div>

                <!-- Schema Selector (only if experiment has schema) -->
                <div v-if="selectedExperiment?.has_schema" class="form-control">
                    <label class="label">
                        <span class="label-text">{{ $t('dashboard.select_schema') }}</span>
                    </label>
                    <select class="select select-bordered w-full">
                        <option value="" disabled selected>
                            {{ $t('dashboard.no_schemas_available') }}
                        </option>
                    </select>
                </div>

                <!-- Experiment Parameters Section (from experiment_commands) -->
                <div v-if="experimentCommandEntries.length > 0" class="card bg-base-200">
                    <div class="card-body p-4">
                        <h4 class="font-semibold text-lg mb-4">
                            {{ $t('dashboard.experiment_parameters') }}
                        </h4>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div
                                v-for="[key, value] in experimentCommandEntries"
                                :key="key"
                                class="form-control"
                            >
                                <label class="label">
                                    <span class="label-text">
                                        {{ key }}
                                    </span>
                                </label>

                                <input
                                    v-model="experimentCommandValues[key]"
                                    type="text"
                                    class="input input-bordered w-full"
                                    :placeholder="key"
                                />
                            </div>
                        </div>

                        <div class="mt-4 flex gap-2 justify-end">
                            <button class="btn btn-primary">
                                {{ $t('dashboard.run_experiment') }}
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Command Selector -->
                <div v-if="commandEntries.length > 0" class="form-control">
                    <label class="label">
                        <span class="label-text">{{ $t('dashboard.select_command') }}</span>
                    </label>
                    <select v-model="selectedCommand" class="select select-bordered w-full">
                        <option v-for="[key, value] in commandEntries" :key="key" :value="key">
                            {{ key }} - {{ value }}
                        </option>
                    </select>
                </div>

                <!-- Selected Experiment Details -->
                <div v-if="selectedExperiment" class="space-y-2">
                    <div class="card bg-base-200">
                        <div class="card-body p-4">
                            <h4 class="font-semibold text-lg">{{ selectedExperiment.name }}</h4>
                            <p v-if="selectedExperiment.description" class="text-sm">
                                {{ selectedExperiment.description }}
                            </p>
                            <div class="divider my-2"></div>
                            <pre class="text-xs bg-base-300 p-3 rounded overflow-auto">{{
                                selectedExperiment
                            }}</pre>
                        </div>
                    </div>
                </div>
            </div>

            <div v-else class="alert alert-warning">
                <span>{{ $t('dashboard.no_experiment_found') }}</span>
            </div>
        </div>
    </div>
</template>
