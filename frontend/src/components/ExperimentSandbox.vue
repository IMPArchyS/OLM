<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { Command, type Reservation } from '@/types/api';
import ExperimentSelector from './ExperimentSelector.vue';
import type { QueueFormData } from '@/types/forms';
import { useExperiments } from '@/composables/useExperiments';
import { useI18n } from 'vue-i18n';
import { useToast } from '@/composables/useToast';
import { useAuthStore } from '@/stores/auth';

const props = defineProps<{ reservation: Reservation }>();

const { t } = useI18n();
const authStore = useAuthStore();
const { showError } = useToast();
const { experimentsByDevice, loading, error, fetchExperimentsByDevice } = useExperiments();

const websocketRef = ref<WebSocket | null>(null);
const websocketMessage = ref('');

function buildWebSocketUrl(accessToken: string) {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin;
    const resolvedApiUrl = new URL(apiBaseUrl, window.location.origin);
    const wsProtocol = resolvedApiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    const websocketUrl = new URL('/ws/reservation/current', `${wsProtocol}//${resolvedApiUrl.host}`);
    websocketUrl.searchParams.set('access_token', accessToken);
    return websocketUrl.toString();
}

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
    const selectedExperiment = experimentsByDevice.value.find((exp) => exp.id === formData.value.id);
    formData.value.output_arguments = selectedExperiment?.output_arguments ?? [];

    console.log(JSON.stringify(formData.value, null, 2));

    websocketMessage.value = '';
    closeWebSocket();

    const accessToken = authStore.accessToken || localStorage.getItem('OLMAccessToken');
    if (!accessToken) {
        websocketMessage.value = 'Authentication required before starting the experiment.';
        showError('Authentication required before starting the experiment.');
        return;
    }

    const websocket = new WebSocket(buildWebSocketUrl(accessToken));
    websocketRef.value = websocket;

    websocket.onopen = () => {
        console.log('WebSocket Created');
        websocket.send(JSON.stringify(formData.value));
    };

    websocket.onmessage = (event) => {
        websocketMessage.value = String(event.data);
        console.log('WebSocket response:', event.data);
    };

    websocket.onerror = (error) => {
        websocketMessage.value = 'WebSocket error. Please try running the experiment again.';
        console.error('WebSocket error:', error);
    };

    websocket.onclose = () => {
        websocketRef.value = null;
        if (!websocketMessage.value) {
            websocketMessage.value = 'WebSocket closed.';
        } else {
            websocketMessage.value = `${websocketMessage.value} (connection closed)`;
        }
        console.log('WebSocket closed');
    };
}

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
            <ExperimentSelector
                fixed-command=""
                :loading="loading"
                :experiments="experimentsByDevice"
                :selected-device-id="props.reservation.device_id"
                @update:formData="handleFormDataUpdate"
            />
            <v-btn
                v-if="experimentsByDevice.length > 0"
                color="info"
                prepend-icon="mdi-plus"
                @click="runExperiment"
                class="mt-4"
                :disabled="formData.id === null"
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
