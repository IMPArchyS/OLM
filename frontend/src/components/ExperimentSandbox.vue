<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { Command, type Reservation } from '@/types/api';
import ExperimentSelector from './ExperimentSelector.vue';
import type { QueueFormData } from '@/types/forms';
import { useExperiments } from '@/composables/useExperiments';
import { useI18n } from 'vue-i18n';
import { useToast } from '@/composables/useToast';

const props = defineProps<{ reservation: Reservation }>();

const { t } = useI18n();
const { showError } = useToast();
const { experimentsByDevice, loading, error, fetchExperimentsByDevice } = useExperiments();

const websocketRef = ref<WebSocket | null>(null);
const websocketMessage = ref('');

function closeWebSocket() {
    const websocket = websocketRef.value;
    if (!websocket) return;

    if (websocket.readyState === WebSocket.OPEN || websocket.readyState === WebSocket.CONNECTING) {
        websocket.close(1000, 'Navigation away from page');
    }

    websocketRef.value = null;
}

onBeforeUnmount(() => {
    closeWebSocket();
});

onBeforeRouteLeave(() => {
    closeWebSocket();
});

function runExperiment() {
    console.log(JSON.stringify(formData.value, null, 2));

    // websocketMessage.value = '';
    // closeWebSocket();

    // const websocket = new WebSocket(`ws://localhost:8000/ws/test`);
    // websocketRef.value = websocket;

    // websocket.onopen = () => {
    //     console.log('WebSocket Created');
    // };

    // websocket.onmessage = (event) => {
    //     websocketMessage.value = String(event.data);
    //     console.log('WebSocket response:', event.data);
    // };

    // websocket.onerror = (error) => {
    //     websocketMessage.value = 'WebSocket error. Please try running the experiment again.';
    //     console.error('WebSocket error:', error);
    // };

    // websocket.onclose = () => {
    //     websocketRef.value = null;
    //     if (!websocketMessage.value) {
    //         websocketMessage.value = 'WebSocket closed.';
    //     } else {
    //         websocketMessage.value = `${websocketMessage.value} (connection closed)`;
    //     }
    //     console.log('WebSocket closed');
    // };
}

const formData = ref<QueueFormData>({
    experiment_id: null,
    command: Command.START,
    input_arguments: {},
    setpoint_changes: {},
    device_id: null,
    software_name: null,
    simulation_time: 0,
    sampling_rate: 0,
});

onMounted(async () => {
    const result = await fetchExperimentsByDevice(props.reservation.device_id);
    if (!result.success) {
        showError(result.message || 'Failed');
    }
});

const handleFormDataUpdate = (data: typeof formData.value) => {
    formData.value = data;
};
</script>

<template>
    <v-card class="mt-4 overflow-auto!">
        <v-card-title>{{ $t('dashboard.ongoing_experiment') }}</v-card-title>

        <v-card-text>
            <ExperimentSelector fixed-command="" :loading="loading" :experiments="experimentsByDevice" @update:formData="handleFormDataUpdate" />
            <v-btn
                v-if="experimentsByDevice.length > 0"
                color="info"
                prepend-icon="mdi-plus"
                @click="runExperiment"
                class="mt-4"
                :disabled="formData.experiment_id === null"
            >
                {{ $t('dashboard.run_experiment') }}
            </v-btn>

            <v-card v-if="websocketMessage" variant="tonal" class="mt-4">
                <v-card-title class="text-subtitle-1">WebSocket messages</v-card-title>
                <v-card-text>
                    <div>{{ websocketMessage }}</div>
                </v-card-text>
            </v-card>
        </v-card-text>
    </v-card>
</template>
