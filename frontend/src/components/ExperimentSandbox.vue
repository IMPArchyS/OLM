<script setup lang="ts">
import { ref } from 'vue'
import type { Reservation } from '@/types/api'
import ExperimentSelector from './ExperimentSelector.vue'

const props = defineProps<{ reservation: Reservation }>()

const experimentSelectorRef = ref<InstanceType<typeof ExperimentSelector> | null>(null)

function runExperiment() {
    const selector = experimentSelectorRef.value
    if (!selector) return

    const selectedExperiment = selector.selectedExperiment
    const selectedCommand = selector.selectedCommand
    const experimentCommandValues = selector.experimentCommandValues

    if (!selectedExperiment) {
        console.error('No experiment selected')
        return
    }

    const missing = Object.entries(selectedExperiment.experiment_commands || {})
        .filter(
            ([key, spec]) =>
                experimentCommandValues[key] === undefined ||
                experimentCommandValues[key] === null ||
                experimentCommandValues[key] === '',
        )
        .map(([key]) => key)

    if (missing.length > 0) {
        alert('Please fill in all experiment command values: ' + missing.join(', '))
        return
    }

    // Reconstruct experiment_commands with full structure (value, type, unit)
    const reconstructedCommands: Record<string, { value: any; type: string; unit?: string }> = {}

    Object.entries(selectedExperiment.experiment_commands || {}).forEach(([key, spec]) => {
        reconstructedCommands[key] = {
            value: experimentCommandValues[key],
            type: spec.type,
            ...(spec.unit && { unit: spec.unit }),
        }
    })

    const payload = {
        experiment_id: selectedExperiment.id,
        command: selectedCommand,
        experiment_commands: reconstructedCommands,
        simulation_time: selector.simTime,
        sampling_rate: selector.sampleRate,
    }
    console.log('Payload to send via WebSocket:', JSON.stringify(payload, null, 2))
    // TODO: Implement WebSocket communication
}
</script>

<template>
    <v-card class="mt-4 overflow-auto!" style="height: calc(100vh - 260px)">
        <v-card-title>{{ $t('dashboard.ongoing_experiment') }}</v-card-title>

        <v-card-text>
            <ExperimentSelector ref="experimentSelectorRef" :device-id="reservation.device_id">
                <template #default>
                    <v-btn color="primary" variant="elevated" @click="runExperiment">
                        {{ $t('dashboard.run_experiment') }}
                    </v-btn>
                </template>
            </ExperimentSelector>
        </v-card-text>
    </v-card>
</template>
