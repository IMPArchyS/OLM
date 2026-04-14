<script setup lang="ts">
import SimpleOutputChart from '@/components/experiments/SimpleOutputChart.vue';
import { useExperimentLogs } from '@/composables/useExperimentLogs';
import { useAuthStore } from '@/stores/auth';
import { useToastStore } from '@/stores/toast';
import type { ExperimentHistoryItem, ExperimentLog, FinishReason } from '@/types/api';
import { computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const authStore = useAuthStore();
const toast = useToastStore();
const { userExperimentLogs, loading, error, fetchExperimentLogsByUser } = useExperimentLogs();

const logs = computed<ExperimentLog[]>(() => {
    return userExperimentLogs.value;
});

const finishReasonLabels: Record<FinishReason, string> = {
    'n/a': 'N/A',
    user_stop: 'User stopped',
    simulation_time_reached: 'Simulation time reached',
    device_timeout: 'Device timeout',
    exception_error: 'Exception error',
};

const formatDateTime = (value?: string | null) => {
    if (!value) {
        return 'N/A';
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString();
};

const formatFinishReason = (reason: FinishReason) => {
    return finishReasonLabels[reason] ?? reason;
};

const getRunStatus = (log: ExperimentLog) => {
    if (!log.started_at) {
        return {
            text: 'Not started',
            color: 'secondary',
        };
    }

    if (!log.finished_at || log.finish_reason === 'n/a') {
        return {
            text: 'Pending',
            color: 'info',
        };
    }

    if (log.finish_reason === 'device_timeout') {
        return {
            text: 'Timed out',
            color: 'warning',
        };
    }

    if (log.finish_reason === 'user_stop') {
        return {
            text: 'Stopped',
            color: 'secondary',
        };
    }

    if (log.finish_reason === 'exception_error') {
        return {
            text: 'Error',
            color: 'error',
        };
    }

    if (log.finish_reason === 'simulation_time_reached' && log.finished_at) {
        return {
            text: 'Finished',
            color: 'success',
        };
    }

    return {
        text: 'Pending',
        color: 'info',
    };
};

const extractTimeSeries = (log: ExperimentLog): number[] => {
    const outputHistory = log.run?.output_history ?? [];

    return outputHistory
        .map((row) => {
            const rawTime = row.time;
            if (typeof rawTime === 'number' && Number.isFinite(rawTime)) {
                return rawTime;
            }

            if (typeof rawTime === 'string') {
                const parsed = Number(rawTime);
                if (Number.isFinite(parsed)) {
                    return parsed;
                }
            }

            return null;
        })
        .filter((value): value is number => value !== null);
};

const estimateSimulationTime = (log: ExperimentLog): number | null => {
    const times = extractTimeSeries(log);
    if (times.length === 0) {
        return null;
    }

    const minTime = Math.min(...times);
    const maxTime = Math.max(...times);
    const duration = maxTime - minTime;

    return Number((duration > 0 ? duration : maxTime).toFixed(3));
};

const estimateSampleInterval = (log: ExperimentLog): number | null => {
    const times = extractTimeSeries(log);
    if (times.length < 2) {
        return null;
    }

    const deltas: number[] = [];
    for (let index = 1; index < times.length; index += 1) {
        const previous = times[index - 1];
        const current = times[index];
        if (previous === undefined || current === undefined) {
            continue;
        }

        const delta = current - previous;
        if (delta > 0 && Number.isFinite(delta)) {
            deltas.push(delta);
        }
    }

    if (deltas.length === 0) {
        return null;
    }

    const averageDelta = deltas.reduce((sum, value) => sum + value, 0) / deltas.length;
    return Number(averageDelta.toFixed(3));
};

const estimateSampleRate = (log: ExperimentLog): number | null => {
    const interval = estimateSampleInterval(log);
    if (!interval || interval <= 0) {
        return null;
    }

    return Number((1 / interval).toFixed(3));
};

const formatArgValue = (rawValue: unknown): string => {
    if (rawValue === null || rawValue === undefined) {
        return 'N/A';
    }

    if (typeof rawValue === 'object' && !Array.isArray(rawValue)) {
        const valueField = (rawValue as { value?: unknown }).value;
        if (valueField !== undefined) {
            return String(valueField);
        }

        return JSON.stringify(rawValue);
    }

    return String(rawValue);
};

const formatArgUnit = (rawValue: unknown): string => {
    if (typeof rawValue === 'object' && rawValue !== null && !Array.isArray(rawValue)) {
        const unitField = (rawValue as { unit?: unknown }).unit;
        if (typeof unitField === 'string' && unitField.trim().length > 0) {
            return unitField;
        }
    }

    return '-';
};

const getInputArgumentRows = (entry: ExperimentHistoryItem): Array<{ key: string; value: string; unit: string }> => {
    return Object.entries(entry.input_args ?? {}).map(([key, rawValue]) => {
        return {
            key,
            value: formatArgValue(rawValue),
            unit: formatArgUnit(rawValue),
        };
    });
};

onMounted(async () => {
    const result = await fetchExperimentLogsByUser(authStore.user?.id);
    if (!result.success) {
        toast.error(result.message || 'Failed');
    }
});
</script>

<template>
    <v-card class="mt-5">
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ t('reports.title') }}</span>
        </v-card-title>
        <v-divider />
        <v-card-text>
            <div v-if="loading" class="py-8 d-flex justify-center">
                <v-progress-circular indeterminate color="primary" size="42" />
            </div>

            <v-alert v-else-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>

            <v-alert v-else-if="logs.length === 0" type="info" variant="tonal"> No report data found for this user. </v-alert>

            <v-expansion-panels v-else variant="accordion">
                <v-expansion-panel v-for="log in logs" :key="log.id" class="mb-3">
                    <v-expansion-panel-title>
                        <div class="d-flex align-center justify-space-between w-100 pr-4">
                            <div>
                                <div class="text-subtitle-1 font-weight-medium">Log #{{ log.id }}</div>
                                <div class="text-caption text-medium-emphasis">Started: {{ formatDateTime(log.started_at) }}</div>
                            </div>
                            <v-chip :color="getRunStatus(log).color" size="small" variant="flat">{{ getRunStatus(log).text }}</v-chip>
                        </div>
                    </v-expansion-panel-title>

                    <v-expansion-panel-text>
                        <div class="mb-4 d-flex flex-wrap ga-2">
                            <v-chip size="small" variant="tonal">Server ID: {{ log.server_id }}</v-chip>
                            <v-chip size="small" variant="tonal">Device ID: {{ log.device_id }}</v-chip>
                            <v-chip size="small" variant="tonal">Started: {{ formatDateTime(log.started_at) }}</v-chip>
                            <v-chip size="small" variant="tonal">Finished: {{ formatDateTime(log.finished_at) }}</v-chip>
                            <v-chip size="small" variant="tonal">Finish reason: {{ formatFinishReason(log.finish_reason) }}</v-chip>

                            <v-chip size="small" variant="tonal">
                                Estimated simulation time: {{ estimateSimulationTime(log) !== null ? `${estimateSimulationTime(log)} s` : 'N/A' }}
                            </v-chip>
                            <v-chip size="small" variant="tonal">
                                Estimated sample interval: {{ estimateSampleInterval(log) !== null ? `${estimateSampleInterval(log)} s` : 'N/A' }}
                            </v-chip>
                            <v-chip size="small" variant="tonal">
                                Estimated sample rate: {{ estimateSampleRate(log) !== null ? `${estimateSampleRate(log)} Hz` : 'N/A' }}
                            </v-chip>
                        </div>

                        <v-alert v-if="!log.run" type="warning" variant="tonal">This log does not contain run data.</v-alert>

                        <v-row v-else dense>
                            <v-col cols="12">
                                <v-card variant="outlined" class="mb-3">
                                    <v-card-title class="d-flex align-center justify-space-between flex-wrap ga-2">
                                        <span class="text-subtitle-1">Run details</span>
                                        <v-chip :color="getRunStatus(log).color" size="small" variant="flat">
                                            {{ getRunStatus(log).text }}
                                        </v-chip>
                                    </v-card-title>
                                    <v-divider />
                                    <v-card-text>
                                        <div class="text-subtitle-2 mt-6 mb-2">Input history</div>
                                        <div v-if="log.run.input_history.length > 0" class="mb-6 input-history-stack">
                                            <v-card
                                                v-for="(entry, index) in log.run.input_history"
                                                :key="`${log.id}-input-${index}`"
                                                variant="outlined"
                                                class="input-entry-card"
                                            >
                                                <v-card-text>
                                                    <div class="d-flex align-center justify-space-between flex-wrap ga-2 mb-3">
                                                        <div class="text-subtitle-2">Entry #{{ index + 1 }}</div>
                                                        <v-chip color="info" size="small" variant="tonal">{{ entry.command }}</v-chip>
                                                    </div>

                                                    <div v-if="getInputArgumentRows(entry).length > 0" class="input-arg-grid">
                                                        <v-sheet
                                                            v-for="item in getInputArgumentRows(entry)"
                                                            :key="`${log.id}-${index}-${item.key}`"
                                                            class="input-arg-item pa-3"
                                                            rounded
                                                            border
                                                        >
                                                            <div class="text-caption text-medium-emphasis">{{ item.key }}</div>
                                                            <div class="text-body-2 font-weight-medium">{{ item.value }}</div>
                                                            <div class="text-caption">Unit: {{ item.unit }}</div>
                                                        </v-sheet>
                                                    </div>
                                                    <v-alert v-else type="info" variant="tonal">No input arguments in this entry.</v-alert>
                                                </v-card-text>
                                            </v-card>
                                        </div>
                                        <v-alert v-else type="info" variant="tonal" class="mb-6">No input history available.</v-alert>

                                        <SimpleOutputChart
                                            :output-history="log.run.output_history"
                                            title="Output history graph"
                                            :height="260"
                                            class="mb-6"
                                        />
                                    </v-card-text>
                                </v-card>
                            </v-col>
                        </v-row>
                    </v-expansion-panel-text>
                </v-expansion-panel>
            </v-expansion-panels>
        </v-card-text>
    </v-card>
</template>

<style scoped>
.input-history-stack {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.input-entry-card {
    background: rgba(var(--v-theme-surface-variant), 0.2);
}

.input-arg-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
}

.input-arg-item {
    background: rgba(var(--v-theme-surface), 0.7);
}
</style>
