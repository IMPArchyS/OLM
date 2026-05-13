<script setup lang="ts">
import ReportLogItem from '@/components/reports/ReportLogItem.vue';
import { useExperimentLogs } from '@/composables/useExperimentLogs';
import { useAuthStore } from '@/stores/auth';
import { useToastStore } from '@/stores/toast';
import type { ExperimentLog } from '@/types/api';
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

const allLogs = computed<ExperimentLog[]>(() => (showAllLogs.value ? experimentLogs.value : userExperimentLogs.value));

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

const totalPages = computed(() => (pageSize.value === -1 ? 1 : Math.ceil(logs.value.length / pageSize.value)));

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

const loadLogs = async () => {
    if (showAllLogs.value) {
        if (!canReadAll.value) {
            showAllLogs.value = false;
            toast.error(t('reports.permissionError'));
            return;
        }
        const result = await fetchExperimentLogs();
        if (!result.success) toast.error(result.message || t('reports.fetchError'));
        return;
    }
    const result = await fetchExperimentLogsByUser();
    if (!result.success) toast.error(result.message || t('reports.fetchError'));
};

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
                    <ReportLogItem
                        v-for="log in paginatedLogs"
                        :key="log.id"
                        :log="log"
                        :show-user-name="showAllLogs"
                        :user-name="log.username"
                        @delete="handleDelete"
                        @restore="handleRestore"
                    />
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
                        <v-pagination
                            v-if="pageSize !== -1 && totalPages > 1"
                            v-model="currentPage"
                            :length="totalPages"
                            :total-visible="7"
                            density="compact"
                        />
                    </div>
                </div>
            </template>
        </v-card-text>
    </v-card>
</template>
