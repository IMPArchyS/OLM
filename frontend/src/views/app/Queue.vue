<script setup lang="ts">
import { ref } from 'vue'
import ExperimentSelector from '@/components/ExperimentSelector.vue'
import { useI18n } from 'vue-i18n'
import type { CommandSpec } from '@/types/api'
import { useDevices } from '@/composables/useDevices'

const { t } = useI18n()

const formData = ref({
    experiment_id: null as number | null,
    command: '',
    experiment_commands: {} as Record<string, CommandSpec>,
    simulation_time: 0,
    sampling_rate: 0,
})

const handleFormDataUpdate = (data: typeof formData.value) => {
    formData.value = data
}

const addToQueue = async () => {
    console.log('Add to queue - Form Data:', JSON.stringify(formData.value, null, 2))

    if (!formData.value.experiment_id) {
        console.error('No experiment selected')
        return
    }

    const { getDeviceByExperimentId } = useDevices()
    const device = await getDeviceByExperimentId(formData.value.experiment_id)

    if (!device) {
        console.error('Device not found for experiment:', formData.value.experiment_id)
        return
    }

    const device_id = device.id
    console.log(JSON.stringify({ device_id, simulation_time: formData.value.simulation_time }))
    try {
        const response = await fetch('http://localhost:8000/api/reservation/queue', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                device_id,
                simulation_time: formData.value.simulation_time,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            }),
        })

        if (!response.ok) {
            const errorData = await response.json()
            alert(`Failed to create reservation: ${errorData.message || response.statusText}`)
            return
        }
    } catch (error) {
        console.error('Error saving reservation:', error)
    }
}
</script>

<template>
    <v-card class="mt-5">
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ t('queues.title') }}</span>
        </v-card-title>
        <v-card-text class="mt-5">
            <ExperimentSelector fixed-command="start" @update:form-data="handleFormDataUpdate" />
            <v-btn color="info" prepend-icon="mdi-plus" @click="addToQueue" class="mt-4">
                {{ t('queues.add_to_queue') }}
            </v-btn>
        </v-card-text>
    </v-card>
</template>
