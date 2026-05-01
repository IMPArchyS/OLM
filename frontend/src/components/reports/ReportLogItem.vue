<script setup lang="ts">
import SimpleOutputChart from '@/components/experiments/SimpleOutputChart.vue';
import type { ExperimentLog } from '@/types/api';
import {
    formatDateTime,
    formatFinishReason,
    formatSampleInterval,
    formatSimTime,
    getFinishReasonColor,
    getInputArgumentRows,
    getLogTitle,
    getRunStatus,
} from '@/utils/reportFormatters';
import { useI18n } from 'vue-i18n';

const props = defineProps<{
    log: ExperimentLog;
    showUserName: boolean;
    userName?: string;
}>();

const emit = defineEmits<{
    delete: [id: number];
    restore: [id: number];
}>();

const { t } = useI18n();
</script>

<template>
    <v-expansion-panel class="mb-3">
        <v-expansion-panel-title :class="{ 'log-deleted': !!log.deleted_at }">
            <div class="d-flex align-center justify-space-between w-100 pr-4">
                <div class="d-flex flex-column">
                    <div class="d-flex align-center ga-2">
                        <span class="text-subtitle-1 font-weight-medium">{{ getLogTitle(log, t) }}</span>
                        <v-chip v-if="showUserName && userName" size="small" variant="tonal" color="primary">{{ userName }}</v-chip>
                        <v-chip v-if="log.deleted_at" size="x-small" variant="tonal" color="error">{{ t('reports.deletedBadge') }}</v-chip>
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
                        @click.stop="emit('delete', log.id)"
                    />
                    <v-btn
                        v-else
                        :title="t('reports.restoreLog')"
                        icon="mdi-restore"
                        size="x-small"
                        variant="text"
                        color="success"
                        @click.stop="emit('restore', log.id)"
                    />
                    <v-chip :color="getRunStatus(log, t).color" size="small" variant="flat">{{ getRunStatus(log, t).text }}</v-chip>
                </div>
            </div>
        </v-expansion-panel-title>

        <v-expansion-panel-text>
            <div class="mb-4 d-flex flex-wrap ga-2">
                <v-chip size="small" variant="tonal"> {{ t('reports.simulationTime') }}: {{ formatSimTime(log) }} </v-chip>
                <v-chip size="small" variant="tonal"> {{ t('reports.sampleInterval') }}: {{ formatSampleInterval(log) }} </v-chip>
                <v-chip :color="getFinishReasonColor(log.finish_reason)" size="small" variant="tonal">
                    {{ t('reports.finishReason') }}: {{ formatFinishReason(log.finish_reason, t) }}
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
                                :x-label="t('dashboard.xLabel')"
                                :y-label="t('dashboard.yLabel')"
                                :height="260"
                                class="mb-6"
                            />
                        </v-card-text>
                    </v-card>
                </v-col>
            </v-row>
        </v-expansion-panel-text>
    </v-expansion-panel>
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
