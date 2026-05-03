<script setup lang="ts">
import { useExperiments } from '@/composables/useExperiments';
import { useDevices } from '@/composables/useDevices';
import router from '@/router';
import { useToastStore } from '@/stores/toast';
import type { Experiment } from '@/types/api';
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const toast = useToastStore();
const { experiments, loading, fetchExperiments, deleteExperiment, restoreExperiment } = useExperiments();
const { devices, fetchDevices } = useDevices();
const showDeletedExperiments = ref(false);
const deletedDeviceIdSet = computed(() => new Set(devices.value.filter((device) => !!device.deleted_at).map((device) => device.id)));

const filteredExperiments = computed(() => {
    if (showDeletedExperiments.value) {
        return experiments.value;
    }

    return experiments.value.filter((experiment) => !experiment.deleted_at);
});

const headers = computed(() => [
    { title: t('common.id'), key: 'id', sortable: true },
    { title: t('experiments.software'), key: 'software', sortable: true },
    { title: t('experiments.devices'), key: 'devices', sortable: false },
    { title: t('experiments.commands'), key: 'commands', sortable: false },
    { title: t('common.actions'), key: 'actions', sortable: false, align: 'center' as const },
]);

onMounted(async () => {
    const [experimentsResult, devicesResult] = await Promise.all([fetchExperiments(), fetchDevices()]);

    if (!experimentsResult.success) {
        toast.error(experimentsResult.message || t('common.error'));
    }

    if (!devicesResult.success) {
        toast.error(devicesResult.message || t('common.error'));
    }
});

const isDeletedExperimentDevice = (device: Experiment['devices'][number]) => {
    return !!device.deleted_at || deletedDeviceIdSet.value.has(device.id);
};

const handleCreate = () => {
    router.push({ name: 'experiments-create' });
};

const handleView = (item: Experiment) => {
    router.push({ name: 'experiments-show', params: { id: item.id } });
};

const handleEdit = (item: Experiment) => {
    router.push({ name: 'experiments-edit', params: { id: item.id } });
};

const handleDelete = async (item: Experiment) => {
    const result = await deleteExperiment(item.id);
    if (result.success) {
        toast.success(result.message || t('experiments.deleted'));
    } else {
        toast.error(result.message || t('common.error'));
    }
};

const handleRestore = async (item: Experiment) => {
    const result = await restoreExperiment(item.id);

    if (result.success) {
        toast.success(result.message || t('experiments.restored'));
    } else {
        toast.error(result.message || t('experiments.restoreUnavailable'));
    }
};
</script>

<template>
    <v-card elevation="4">
        <v-card-title class="bg-card-title d-flex align-center flex-wrap ga-3">
            <v-icon icon="mdi-flask" class="mr-2" />
            <span>{{ t('nav.experiments') }}</span>
            <v-spacer />
            <v-switch v-model="showDeletedExperiments" :label="t('common.showDeleted')" color="info" hide-details density="compact" />
            <v-btn color="primary" variant="flat" prepend-icon="mdi-plus" @click="handleCreate">
                {{ t('actions.create') }}
            </v-btn>
        </v-card-title>
        <v-divider />

        <v-data-table
            :headers="headers"
            :items="filteredExperiments"
            :loading="loading"
            :row-props="({ item }) => ({ class: item.deleted_at ? 'text-error' : '' })"
            item-value="id"
        >
            <template #item.software="{ item }">
                {{ item.software?.name || t('experiments.noSoftware') }}
            </template>

            <template #item.devices="{ item }">
                <div class="py-2">
                    <div class="d-flex flex-wrap ga-1">
                        <v-chip
                            v-for="device in item.devices"
                            :key="device.id"
                            size="small"
                            :variant="item.deleted_at || isDeletedExperimentDevice(device) ? 'tonal' : 'outlined'"
                            :color="item.deleted_at ? 'error' : isDeletedExperimentDevice(device) ? 'warning' : undefined"
                            :prepend-icon="isDeletedExperimentDevice(device) ? 'mdi-alert-circle' : undefined"
                            :class="item.deleted_at || isDeletedExperimentDevice(device) ? 'font-weight-medium' : ''"
                        >
                            {{ device.name }}
                        </v-chip>
                        <span v-if="item.devices.length === 0" class="text-medium-emphasis">{{ t('experiments.noDevices') }}</span>
                    </div>
                </div>
            </template>

            <template #item.commands="{ item }">
                <div class="d-flex flex-wrap ga-1 py-2">
                    <v-chip
                        v-for="command in item.commands"
                        :key="`${item.id}-${command}`"
                        size="small"
                        :color="item.deleted_at ? 'error' : 'info'"
                        variant="tonal"
                    >
                        {{ command }}
                    </v-chip>
                </div>
            </template>

            <template #item.actions="{ item }">
                <v-btn icon="mdi-eye" size="small" variant="text" color="warning" @click.stop="handleView(item)" />
                <v-btn v-if="!item.deleted_at" icon="mdi-pencil" size="small" variant="text" color="primary" @click.stop="handleEdit(item)" />
                <v-btn v-if="!item.deleted_at" icon="mdi-trash-can" size="small" variant="text" color="error" @click.stop="handleDelete(item)" />
                <v-btn v-if="item.deleted_at" icon="mdi-restore" size="small" variant="text" color="secondary" @click.stop="handleRestore(item)" />
            </template>
        </v-data-table>
    </v-card>
</template>
