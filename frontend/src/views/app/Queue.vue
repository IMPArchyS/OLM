<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import ExperimentSelector from '@/components/experiments/ExperimentSelector.vue';
import { useI18n } from 'vue-i18n';
import { Command } from '@/types/api';
import type { QueueFormData } from '@/types/forms';
import { useExperiments } from '@/composables/useExperiments';
import { useServers } from '@/composables/useServers';
import { useDevices } from '@/composables/useDevices';
import { useAuthStore } from '@/stores/auth';
import { useToastStore } from '@/stores/toast';

const { t } = useI18n();
const toast = useToastStore();
const authStore = useAuthStore();
const { experimentsByDevice, loading, queueSelectedExperiment, fetchExperimentsByDevice } = useExperiments();
const { servers, fetchServers } = useServers();
const { devices, fetchDevicesByServer } = useDevices();

const selectedServerId = ref<number | null>(null);
const selectedDeviceId = ref<number | null>(null);

const selectableServers = computed(() => {
    return servers.value.filter((server) => !server.deleted_at && server.available && server.enabled && server.production);
});

const selectableDevices = computed(() => {
    return devices.value.filter((device) => !device.deleted_at);
});

const selectableExperiments = computed(() => {
    return selectedDeviceId.value ? experimentsByDevice.value : [];
});

const formData = ref<QueueFormData>({
    user_id: authStore.user?.id ?? null,
    id: null,
    command: Command.START,
    input_arguments: {},
    output_arguments: [],
    setpoint_changes: {},
    schema_id: null,
    device_id: null,
    software_name: null,
    simulation_time: 0,
    sample_rate: 0,
});

onMounted(async () => {
    await fetchServers();
});

watch(selectedServerId, async (newServerId) => {
    selectedDeviceId.value = null;
    formData.value.id = null;

    if (!newServerId) {
        return;
    }

    await fetchDevicesByServer(newServerId);
});

watch(selectedDeviceId, async (newDeviceId) => {
    formData.value.id = null;
    if (!newDeviceId) {
        return;
    }

    const result = await fetchExperimentsByDevice(newDeviceId);
    if (!result.success) {
        toast.error(result.message || 'Failed');
    }
});

const handleFormDataUpdate = (data: typeof formData.value) => {
    formData.value = {
        ...data,
        device_id: selectedDeviceId.value,
    };
};

const addToQueue = async () => {
    const selectedExperiment = selectableExperiments.value.find((exp) => exp.id === formData.value.id);
    formData.value.output_arguments = selectedExperiment?.output_arguments ?? [];

    console.log(JSON.stringify(formData.value, null, 2));
    const result = await queueSelectedExperiment(formData.value);

    if (result.success) {
        toast.success(result.message ?? 'queued');
        return;
    }

    toast.error(result.message ?? 'failed');
};
</script>

<template>
    <v-card class="queue-card">
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ t('queues.title') }}</span>
        </v-card-title>
        <v-card-text class="queue-card__body">
            <div class="queue-layout">
                <div class="queue-top-row">
                <v-select
                    v-model="selectedServerId"
                    :items="selectableServers"
                    item-title="name"
                    item-value="id"
                    label="Select server"
                    variant="outlined"
                    density="comfortable"
                    class="queue-field"
                />

                <v-select
                    v-model="selectedDeviceId"
                    :items="selectableDevices"
                    item-title="name"
                    item-value="id"
                    :disabled="!selectedServerId"
                    label="Select device"
                    variant="outlined"
                    density="comfortable"
                    class="queue-field"
                />
                </div>

                <ExperimentSelector
                    fixed-command="start"
                    :loading="loading"
                    :experiments="selectableExperiments"
                    :selected-device-id="selectedDeviceId"
                    compact
                    class="queue-field"
                    @update:formData="handleFormDataUpdate"
                />
            </div>

            <div class="queue-action">
                <v-btn
                    v-if="selectableExperiments.length > 0"
                    color="info"
                    prepend-icon="mdi-plus"
                    @click="addToQueue"
                    :disabled="formData.id === null || selectedServerId === null || selectedDeviceId === null"
                >
                    {{ t('queues.add_to_queue') }}
                </v-btn>
            </div>
        </v-card-text>
    </v-card>
</template>

<style scoped>
.queue-card {
    width: 100%;
    margin: 0 auto;
}

.queue-card__body {
    padding-top: 20px;
}

.queue-layout {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.queue-top-row {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.queue-field {
    min-width: 0;
}

.queue-action {
    margin-top: 16px;
}

@media (max-width: 960px) {
    .queue-top-row {
        grid-template-columns: minmax(0, 1fr);
    }

    .queue-action :deep(.v-btn) {
        width: 100%;
    }
}
</style>
