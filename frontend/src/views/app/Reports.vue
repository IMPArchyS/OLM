<script setup lang="ts">
import ExperimentOutputChart from '@/components/ExperimentOutputChart.vue';
import { useExperimentLogs } from '@/composables/useExperimentLogs';
import { useToast } from '@/composables/useToast';
import { useAuthStore } from '@/stores/auth';
import type { ExperimentLog, ExperimentRun } from '@/types/api';
import { computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const authStore = useAuthStore();
const { showError } = useToast();
const { userExperimentLogs, loading, error, fetchExperimentLogsByUser } = useExperimentLogs();

type ReportRun = Omit<ExperimentRun, 'output_history' | 'finished_at' | 'stopped_at' | 'timedout_at'> & {
    output_history: Record<string, unknown>[];
    finished_at?: string | null;
    stopped_at?: string | null;
    timedout_at?: string | null;
};

type ReportLog = Omit<ExperimentLog, 'runs'> & {
    user_id?: number;
    note?: string | null;
    modified_at?: string;
    deleted_at?: string | null;
    runs: ReportRun[];
};

const logs = computed<ReportLog[]>(() => {
    return userExperimentLogs.value as ReportLog[];
});

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

const getRunStatus = (run: ReportRun) => {
    if (run.timedout_at) {
        return {
            text: 'Timed out',
            color: 'warning',
        };
    }

    if (run.stopped_at) {
        return {
            text: 'Stopped',
            color: 'secondary',
        };
    }

    if (run.finished_at) {
        return {
            text: 'Finished',
            color: 'success',
        };
    }

    return {
        text: 'Running',
        color: 'info',
    };
};

const getOutputColumns = (run: ReportRun) => {
    const columns = new Set<string>();

    for (const row of run.output_history) {
        Object.keys(row).forEach((key) => columns.add(key));
    }

    return Array.from(columns);
};

const formatValue = (value: unknown) => {
    if (value === null || value === undefined) {
        return 'N/A';
    }

    if (typeof value === 'number') {
        return Number.isInteger(value) ? value : value.toFixed(4);
    }

    if (typeof value === 'object') {
        return JSON.stringify(value);
    }

    return String(value);
};

onMounted(async () => {
    const result = await fetchExperimentLogsByUser(authStore.user?.id);
    if (!result.success) {
        showError(result.message || 'Failed');
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
                                <div class="text-caption text-medium-emphasis">Created: {{ formatDateTime(log.created_at) }}</div>
                            </div>
                            <v-chip size="small" color="primary" variant="flat">{{ log.runs.length }} run(s)</v-chip>
                        </div>
                    </v-expansion-panel-title>

                    <v-expansion-panel-text>
                        <div class="mb-4 d-flex flex-wrap ga-2">
                            <v-chip v-if="log.user_id" size="small" variant="tonal">User ID: {{ log.user_id }}</v-chip>
                            <v-chip size="small" variant="tonal">Created: {{ formatDateTime(log.created_at) }}</v-chip>
                            <v-chip size="small" variant="tonal">Modified: {{ formatDateTime(log.modified_at) }}</v-chip>
                        </div>

                        <v-alert v-if="log.note" type="info" variant="tonal" class="mb-4">{{ log.note }}</v-alert>

                        <v-alert v-if="log.runs.length === 0" type="warning" variant="tonal">This log does not contain any runs.</v-alert>

                        <v-row v-else dense>
                            <v-col v-for="(run, runIndex) in log.runs" :key="`${log.id}-${runIndex}`" cols="12">
                                <v-card variant="outlined" class="mb-3">
                                    <v-card-title class="d-flex align-center justify-space-between flex-wrap ga-2">
                                        <span class="text-subtitle-1">Run {{ runIndex + 1 }}</span>
                                        <v-chip :color="getRunStatus(run).color" size="small" variant="flat">
                                            {{ getRunStatus(run).text }}
                                        </v-chip>
                                    </v-card-title>
                                    <v-divider />
                                    <v-card-text>
                                        <v-row dense>
                                            <v-col cols="12" md="4">
                                                <div class="text-caption text-medium-emphasis">Started at</div>
                                                <div>{{ formatDateTime(run.started_at) }}</div>
                                            </v-col>
                                            <v-col cols="12" md="4">
                                                <div class="text-caption text-medium-emphasis">Finished at</div>
                                                <div>{{ formatDateTime(run.finished_at) }}</div>
                                            </v-col>
                                            <v-col cols="12" md="4">
                                                <div class="text-caption text-medium-emphasis">Stopped at</div>
                                                <div>{{ formatDateTime(run.stopped_at) }}</div>
                                            </v-col>
                                        </v-row>

                                        <div class="text-subtitle-2 mt-6 mb-2">Input history</div>
                                        <v-table density="compact" class="mb-6">
                                            <thead>
                                                <tr>
                                                    <th>Command</th>
                                                    <th>Input arguments</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr v-for="(entry, index) in run.input_history" :key="`${runIndex}-input-${index}`">
                                                    <td>{{ entry.command }}</td>
                                                    <td>
                                                        <pre class="text-caption mb-0">{{ JSON.stringify(entry.input_args, null, 2) }}</pre>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </v-table>

                                        <experiment-output-chart :output-history="run.output_history" title="Output history graph" class="mb-6" />

                                        <div class="text-subtitle-2 mb-2">Output history rows</div>
                                        <v-table density="compact" fixed-header height="240">
                                            <thead>
                                                <tr>
                                                    <th v-for="column in getOutputColumns(run)" :key="column">{{ column }}</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr v-for="(row, rowIndex) in run.output_history" :key="`${runIndex}-row-${rowIndex}`">
                                                    <td v-for="column in getOutputColumns(run)" :key="`${runIndex}-row-${rowIndex}-${column}`">
                                                        {{ formatValue(row[column]) }}
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </v-table>
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
