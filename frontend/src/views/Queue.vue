<script setup lang="ts">
import { ref } from 'vue'
import ExperimentSelector from '@/components/ExperimentSelector.vue'
import { useI18n } from 'vue-i18n'
import type { CommandSpec } from '@/types/api'

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

    // TODO: Send to backend
    // await fetch('/api/queue', {
    //     method: 'POST',
    //     body: JSON.stringify(formData.value)
    // })
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
