<script setup lang="ts">
import { useExperimentLogs } from '@/composables/useExperimentLogs';
import { useAuthStore } from '@/stores/auth';
import { useToastStore } from '@/stores/toast';
import type { ExperimentLog, ExperimentRun, SoftwareName } from '@/types/api';
import { computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const authStore = useAuthStore();
const toast = useToastStore();
const { userExperimentLogs, loading, error, fetchExperimentLogsByUser } = useExperimentLogs();

const logs = computed<ExperimentLog[]>(() => {
    return userExperimentLogs.value;
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

const getRunStatus = (log: ExperimentLog) => {
    if (log.timedout_at) {
        return {
            text: 'Timed out',
            color: 'warning',
        };
    }

    if (log.stopped_at) {
        return {
            text: 'Stopped',
            color: 'secondary',
        };
    }

    if (log.finished_at) {
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

const getOutputColumns = (run: ExperimentRun) => {
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

const formatSoftwareName = (softwareName: SoftwareName) => {
    const softwareLabels: Record<SoftwareName, string> = {
        openloop: 'OpenLoop',
        matlab: 'MATLAB',
        scilab: 'Scilab',
        openmodelica: 'OpenModelica',
    };

    return softwareLabels[softwareName] || softwareName;
};

onMounted(async () => {
    const result = await fetchExperimentLogsByUser(authStore.user?.id);
    if (!result.success) {
        toast.error(result.message || 'Failed');
    }
});
</script>

<template>
    <v-card>
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
                            <v-chip size="small" variant="tonal">Software: {{ formatSoftwareName(log.software_name) }}</v-chip>
                            <v-chip size="small" variant="tonal">Started: {{ formatDateTime(log.started_at) }}</v-chip>
                            <v-chip size="small" variant="tonal">Finished: {{ formatDateTime(log.finished_at) }}</v-chip>
                            <v-chip size="small" variant="tonal">Stopped: {{ formatDateTime(log.stopped_at) }}</v-chip>
                            <v-chip size="small" variant="tonal">Timed out: {{ formatDateTime(log.timedout_at) }}</v-chip>
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
                                        <v-table v-if="log.run.input_history.length > 0" density="compact" class="mb-6">
                                            <thead>
                                                <tr>
                                                    <th>Command</th>
                                                    <th>Input arguments</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr v-for="(entry, index) in log.run.input_history" :key="`${log.id}-input-${index}`">
                                                    <td>{{ entry.command }}</td>
                                                    <td>
                                                        <pre class="text-caption mb-0">{{ JSON.stringify(entry.input_args, null, 2) }}</pre>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </v-table>
                                        <v-alert v-else type="info" variant="tonal" class="mb-6">No input history available.</v-alert>

                                        <experiment-output-chart :output-history="log.run.output_history" title="Output history graph" class="mb-6" />
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
