<script setup lang="ts">
import SimpleOutputChart from '@/components/experiments/SimpleOutputChart.vue';
import { useExperimentLogs } from '@/composables/useExperimentLogs';
import { apiClient } from '@/lib/apiClient';
import { useAuthStore } from '@/stores/auth';
import { useToastStore } from '@/stores/toast';
import type { ExperimentHistoryItem, ExperimentLog, FinishReason } from '@/types/api';
import { computed, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const authStore = useAuthStore();
const toast = useToastStore();
const {
    experimentLogs,
    userExperimentLogs,
    loading,
    error,
    fetchExperimentLogs,
    fetchExperimentLogsByUser,
    deleteExperimentLog,
    restoreExperimentLog,
} = useExperimentLogs();
const canReadAll = computed(() => authStore.can('olm.experiment_log.read_all'));
const showAllLogs = ref(false);

type DeletedFilter = 'active' | 'deleted' | 'all';
const deletedFilter = ref<DeletedFilter>('active');

const pageSizeOptions = computed(() => [
    { title: '10', value: 10 },
    { title: '25', value: 25 },
    { title: '100', value: 100 },
    { title: t('reports.all'), value: -1 },
]);
const pageSize = ref(10);
const currentPage = ref(1);

const allLogs = computed<ExperimentLog[]>(() => {
    return showAllLogs.value ? experimentLogs.value : userExperimentLogs.value;
});

const logs = computed<ExperimentLog[]>(() => {
    switch (deletedFilter.value) {
        case 'active':
            return allLogs.value.filter((l) => !l.deleted_at);
        case 'deleted':
            return allLogs.value.filter((l) => !!l.deleted_at);
        default:
            return allLogs.value;
    }
});

const totalPages = computed(() => {
    if (pageSize.value === -1) return 1;
    return Math.ceil(logs.value.length / pageSize.value);
});

const paginatedLogs = computed(() => {
    if (pageSize.value === -1) return logs.value;
    const start = (currentPage.value - 1) * pageSize.value;
    return logs.value.slice(start, start + pageSize.value);
});

const paginationFrom = computed(() => {
    if (pageSize.value === -1 || logs.value.length === 0) return logs.value.length === 0 ? 0 : 1;
    return (currentPage.value - 1) * pageSize.value + 1;
});

const paginationTo = computed(() => {
    if (pageSize.value === -1) return logs.value.length;
    return Math.min(currentPage.value * pageSize.value, logs.value.length);
});

watch(allLogs, () => {
    currentPage.value = 1;
});

watch(pageSize, () => {
    currentPage.value = 1;
});

watch(deletedFilter, () => {
    currentPage.value = 1;
});

const handleDelete = async (id: number) => {
    const result = await deleteExperimentLog(id);
    if (result.success) {
        toast.success(t('reports.deleteSuccess'));
        await loadLogs();
    } else {
        toast.error(result.message || t('reports.fetchError'));
    }
};

const handleRestore = async (id: number) => {
    const result = await restoreExperimentLog(id);
    if (result.success) {
        toast.success(t('reports.restoreSuccess'));
        await loadLogs();
    } else {
        toast.error(result.message || t('reports.fetchError'));
    }
};

const userNames = ref(new Map<number, string>());

const fetchUserNames = async (logList: ExperimentLog[]) => {
    const uniqueIds = [...new Set(logList.map((l) => l.user_id))];
    const results = await Promise.allSettled(uniqueIds.map((id) => apiClient.get(`/auth/user/${id}`)));
    const map = new Map<number, string>();
    results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
            const id = uniqueIds[index];
            const name: string | undefined = result.value.data?.name;
            if (id !== undefined && name) map.set(id, name);
        }
    });
    userNames.value = map;
};

const finishReasonColorMap: Record<FinishReason, string> = {
    'n/a': 'secondary',
    user_stop: 'secondary',
    simulation_time_reached: 'success',
    device_timeout: 'warning',
    exception_error: 'error',
};

const finishReasonI18nKey: Record<FinishReason, string> = {
    'n/a': 'reports.finishReasons.na',
    user_stop: 'reports.finishReasons.userStop',
    simulation_time_reached: 'reports.finishReasons.simulationTimeReached',
    device_timeout: 'reports.finishReasons.deviceTimeout',
    exception_error: 'reports.finishReasons.exceptionError',
};

const formatDateTime = (value?: string | null) => {
    if (!value) return 'N/A';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
};

const getLogTitle = (log: ExperimentLog): string => {
    const server = log.server_name ?? String(log.server_id);
    const device = log.device_name ?? String(log.device_id);
    const parts = [server, device];
    if (log.software_name) parts.push(log.software_name);
    return `${t('reports.logPrefix')} - ${parts.join(' | ')}`;
};

const formatFinishReason = (reason: FinishReason): string => {
    return t(finishReasonI18nKey[reason] ?? 'reports.finishReasons.na');
};

const getFinishReasonColor = (reason: FinishReason): string => {
    return finishReasonColorMap[reason] ?? 'secondary';
};

const getRunStatus = (log: ExperimentLog) => {
    if (!log.started_at) return { text: t('reports.status.notStarted'), color: 'secondary' };
    if (!log.finished_at || log.finish_reason === 'n/a') return { text: t('reports.status.pending'), color: 'info' };
    if (log.finish_reason === 'device_timeout') return { text: t('reports.status.timedOut'), color: 'warning' };
    if (log.finish_reason === 'user_stop') return { text: t('reports.status.stopped'), color: 'secondary' };
    if (log.finish_reason === 'exception_error') return { text: t('reports.status.error'), color: 'error' };
    if (log.finish_reason === 'simulation_time_reached' && log.finished_at) return { text: t('reports.status.finished'), color: 'success' };
    return { text: t('reports.status.pending'), color: 'info' };
};

const extractTimeSeries = (log: ExperimentLog): number[] => {
    const outputHistory = log.run?.output_history ?? [];
    return outputHistory
        .map((row) => {
            const rawTime = row.time;
            if (typeof rawTime === 'number' && Number.isFinite(rawTime)) return rawTime;
            if (typeof rawTime === 'string') {
                const parsed = Number(rawTime);
                if (Number.isFinite(parsed)) return parsed;
            }
            return null;
        })
        .filter((value): value is number => value !== null);
};

const estimateSimulationTime = (log: ExperimentLog): number | null => {
    const times = extractTimeSeries(log);
    if (times.length === 0) return null;
    const minTime = Math.min(...times);
    const maxTime = Math.max(...times);
    const duration = maxTime - minTime + 1;
    return Number((duration > 0 ? duration : maxTime).toFixed(3));
};

const estimateSampleInterval = (log: ExperimentLog): number | null => {
    const times = extractTimeSeries(log);
    if (times.length < 2) return null;
    const deltas: number[] = [];
    for (let index = 1; index < times.length; index += 1) {
        const previous = times[index - 1];
        const current = times[index];
        if (previous === undefined || current === undefined) continue;
        const delta = current - previous;
        if (delta > 0 && Number.isFinite(delta)) deltas.push(delta);
    }
    if (deltas.length === 0) return null;
    const averageDelta = deltas.reduce((sum, value) => sum + value, 0) / deltas.length;
    return Number(averageDelta.toFixed(3));
};

const formatArgValue = (rawValue: unknown): string => {
    if (rawValue === null || rawValue === undefined) return 'N/A';
    if (typeof rawValue === 'object' && !Array.isArray(rawValue)) {
        const valueField = (rawValue as { value?: unknown }).value;
        if (valueField !== undefined) return String(valueField);
        return JSON.stringify(rawValue);
    }
    return String(rawValue);
};

const formatArgUnit = (rawValue: unknown): string => {
    if (typeof rawValue === 'object' && rawValue !== null && !Array.isArray(rawValue)) {
        const unitField = (rawValue as { unit?: unknown }).unit;
        if (typeof unitField === 'string' && unitField.trim().length > 0) return unitField;
    }
    return '-';
};

const getInputArgumentRows = (entry: ExperimentHistoryItem): Array<{ key: string; value: string; unit: string }> => {
    return Object.entries(entry.input_args ?? {}).map(([key, rawValue]) => ({
        key,
        value: formatArgValue(rawValue),
        unit: formatArgUnit(rawValue),
    }));
};

const loadLogs = async () => {
    if (showAllLogs.value) {
        if (!canReadAll.value) {
            showAllLogs.value = false;
            toast.error(t('reports.permissionError'));
            return;
        }
        const result = await fetchExperimentLogs();
        if (!result.success) {
            toast.error(result.message || t('reports.fetchError'));
            return;
        }
        await fetchUserNames(experimentLogs.value);
        return;
    }
    userNames.value = new Map();
    const result = await fetchExperimentLogsByUser(authStore.user?.id);
    if (!result.success) toast.error(result.message || t('reports.fetchError'));
};

watch(showAllLogs, async () => {
    await loadLogs();
});

onMounted(async () => {
    await loadLogs();
});
</script>

<template>
    <v-card elevation="4">
        <v-card-title class="bg-card-title d-flex align-center">
            <v-icon icon="mdi-file-document-outline" class="mr-2" />
            <span>{{ t('nav.reports') }}</span>
            <v-spacer />
            <v-switch v-if="canReadAll" v-model="showAllLogs" color="primary" density="compact" hide-details :label="t('reports.showAll')" />
        </v-card-title>
        <v-divider />
        <div class="d-flex align-center px-4 py-2">
            <v-btn-toggle v-model="deletedFilter" density="compact" variant="outlined" mandatory color="primary">
                <v-btn value="active" size="small">{{ t('reports.filterActive') }}</v-btn>
                <v-btn value="deleted" size="small">{{ t('reports.filterDeleted') }}</v-btn>
                <v-btn value="all" size="small">{{ t('reports.filterAll') }}</v-btn>
            </v-btn-toggle>
        </div>
        <v-divider />
        <v-card-text>
            <div v-if="loading" class="py-8 d-flex justify-center">
                <v-progress-circular indeterminate color="primary" size="42" />
            </div>

            <v-alert v-else-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>

            <v-alert v-else-if="logs.length === 0" type="info" variant="tonal">{{ t('reports.noData') }}</v-alert>

            <template v-else>
                <v-expansion-panels variant="accordion">
                    <v-expansion-panel v-for="log in paginatedLogs" :key="log.id" class="mb-3">
                        <v-expansion-panel-title :class="{ 'log-deleted': !!log.deleted_at }">
                            <div class="d-flex align-center justify-space-between w-100 pr-4">
                                <div class="d-flex flex-column">
                                    <div class="d-flex align-center ga-2">
                                        <span class="text-subtitle-1 font-weight-medium">{{ getLogTitle(log) }}</span>
                                        <v-chip v-if="showAllLogs && userNames.has(log.user_id)" size="small" variant="tonal" color="primary">{{
                                            userNames.get(log.user_id)
                                        }}</v-chip>
                                        <v-chip v-if="log.deleted_at" size="x-small" variant="tonal" color="error">{{
                                            t('reports.deletedBadge')
                                        }}</v-chip>
                                    </div>
                                    <div class="text-caption text-medium-emphasis">
                                        {{ t('reports.started') }}: {{ formatDateTime(log.started_at) }} &middot; {{ t('reports.finished') }}:
                                        {{ formatDateTime(log.finished_at) }}
                                    </div>
                                </div>
                                <div class="d-flex align-center ga-1">
                                    <v-btn
                                        v-if="!log.deleted_at"
                                        :title="t('reports.deleteLog')"
                                        icon="mdi-trash-can"
                                        size="x-small"
                                        variant="text"
                                        color="error"
                                        @click.stop="handleDelete(log.id)"
                                    />
                                    <v-btn
                                        v-else
                                        :title="t('reports.restoreLog')"
                                        icon="mdi-restore"
                                        size="x-small"
                                        variant="text"
                                        color="success"
                                        @click.stop="handleRestore(log.id)"
                                    />
                                    <v-chip :color="getRunStatus(log).color" size="small" variant="flat">{{ getRunStatus(log).text }}</v-chip>
                                </div>
                            </div>
                        </v-expansion-panel-title>

                        <v-expansion-panel-text>
                            <div class="mb-4 d-flex flex-wrap ga-2">
                                <v-chip size="small" variant="tonal">
                                    {{ t('reports.simulationTime') }}:
                                    {{ estimateSimulationTime(log) !== null ? `${estimateSimulationTime(log)} s` : 'N/A' }}
                                </v-chip>
                                <v-chip size="small" variant="tonal">
                                    {{ t('reports.sampleInterval') }}:
                                    {{ estimateSampleInterval(log) !== null ? `${estimateSampleInterval(log)} s` : 'N/A' }}
                                </v-chip>
                                <v-chip :color="getFinishReasonColor(log.finish_reason)" size="small" variant="tonal">
                                    {{ t('reports.finishReason') }}: {{ formatFinishReason(log.finish_reason) }}
                                </v-chip>
                            </div>

                            <v-alert v-if="!log.run" type="warning" variant="tonal">{{ t('reports.noRunData') }}</v-alert>

                            <v-row v-else dense>
                                <v-col cols="12">
                                    <v-card class="mb-3 run-details-card">
                                        <v-card-title class="text-subtitle-1">{{ t('reports.runDetails') }}</v-card-title>
                                        <v-divider />
                                        <v-card-text>
                                            <div class="text-subtitle-2 mt-6 mb-2">{{ t('reports.inputHistory') }}</div>
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
                                                                <div class="text-caption">{{ t('reports.unit') }}: {{ item.unit }}</div>
                                                            </v-sheet>
                                                        </div>
                                                        <v-alert v-else type="info" variant="tonal">{{ t('reports.noInputArgs') }}</v-alert>
                                                    </v-card-text>
                                                </v-card>
                                            </div>
                                            <v-alert v-else type="info" variant="tonal" class="mb-6">{{ t('reports.noInputHistory') }}</v-alert>

                                            <SimpleOutputChart
                                                :output-history="log.run.output_history"
                                                :title="t('reports.outputHistoryTitle')"
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

                <div class="d-flex align-center justify-space-between flex-wrap ga-2 mt-4">
                    <div class="d-flex align-center ga-2">
                        <span class="text-caption text-medium-emphasis">{{ t('reports.itemsPerPage') }}:</span>
                        <v-select
                            v-model="pageSize"
                            :items="pageSizeOptions"
                            density="compact"
                            variant="outlined"
                            hide-details
                            style="min-width: 90px; max-width: 110px"
                        />
                    </div>
                    <div class="d-flex align-center ga-2">
                        <span class="text-caption text-medium-emphasis">
                            {{ paginationFrom }}&ndash;{{ paginationTo }} {{ t('reports.of') }} {{ logs.length }}
                        </span>
                        <v-pagination v-if="pageSize !== -1 && totalPages > 1" v-model="currentPage" :length="totalPages" density="compact" />
                    </div>
                </div>
            </template>
        </v-card-text>
    </v-card>
</template>

<style scoped>
.log-deleted {
    opacity: 0.6;
}

.run-details-card {
    border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.input-history-stack {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.input-entry-card {
    background: rgba(var(--v-theme-surface-variant), 0.2);
    border-color: rgba(var(--v-theme-on-surface), 0.18) !important;
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
