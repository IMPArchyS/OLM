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
const { experiments, loading, error, fetchExperiments, deleteExperiment, restoreExperiment } = useExperiments();
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
    { title: t('experiments.id'), key: 'id', sortable: true },
    { title: t('experiments.software'), key: 'software', sortable: true },
    { title: t('experiments.devices'), key: 'devices', sortable: false },
    { title: t('experiments.commands'), key: 'commands', sortable: false },
    { title: t('experiments.actions'), key: 'actions', sortable: false, align: 'center' as const },
]);

onMounted(async () => {
    const [experimentsResult, devicesResult] = await Promise.all([fetchExperiments(), fetchDevices()]);

    if (!experimentsResult.success) {
        toast.error(experimentsResult.message || 'Failed');
    }

    if (!devicesResult.success) {
        toast.error(devicesResult.message || 'Failed');
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
    const shouldDelete = window.confirm(t('experiments.confirmDelete'));
    if (!shouldDelete) {
        return;
    }

    const result = await deleteExperiment(item.id);
    if (result.success) {
        toast.success(result.message || t('experiments.deleted'));
    } else {
        toast.error(result.message || 'Failed');
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

const formatInputArgument = (value: unknown) => {
    if (typeof value === 'number') {
        return value;
    }

    if (typeof value === 'string') {
        return value;
    }

    return '';
};
</script>

<template>
    <v-card>
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ t('experiments.title') }}</span>
        </v-card-title>
        <v-divider />

        <v-container fluid>
            <v-data-table
                :headers="headers"
                :items="filteredExperiments"
                :loading="loading"
                :loading-text="t('experiments.loading')"
                class="elevation-1"
                item-value="id"
            >
                <template #top>
                    <v-toolbar flat density="comfortable" class="px-2">
                        <v-toolbar-title class="text-h6">
                            {{ t('experiments.listTitle') }}
                        </v-toolbar-title>
                        <v-spacer />
                        <div class="d-flex align-center flex-wrap justify-end ga-3">
                            <v-switch v-model="showDeletedExperiments" :label="t('experiments.showDeleted')" color="info" hide-details />
                            <v-btn color="primary" variant="flat" prepend-icon="mdi-plus" @click="handleCreate">
                                {{ t('experiments.addExperiment') }}
                            </v-btn>
                        </div>
                    </v-toolbar>
                    <v-divider />
                </template>

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
                                :variant="isDeletedExperimentDevice(device) ? 'tonal' : 'outlined'"
                                :color="isDeletedExperimentDevice(device) ? 'warning' : undefined"
                                :prepend-icon="isDeletedExperimentDevice(device) ? 'mdi-alert-circle' : undefined"
                                :class="isDeletedExperimentDevice(device) ? 'font-weight-medium' : ''"
                            >
                                {{ device.name }}
                            </v-chip>
                            <span v-if="item.devices.length === 0" class="text-medium-emphasis">{{ t('experiments.noDevices') }}</span>
                        </div>
                    </div>
                </template>

                <template #item.commands="{ item }">
                    <div class="d-flex flex-wrap ga-1 py-2">
                        <v-chip v-for="command in item.commands" :key="`${item.id}-${command}`" size="small" color="info" variant="tonal">
                            {{ command }}
                        </v-chip>
                    </div>
                </template>

                <template #item.actions="{ item }">
                    <v-btn icon="mdi-eye" size="small" variant="text" color="warning" @click.stop="handleView(item)" />
                    <v-btn v-if="!item.deleted_at" icon="mdi-pencil" size="small" variant="text" color="primary" @click.stop="handleEdit(item)" />
                    <v-btn v-if="!item.deleted_at" icon="mdi-delete" size="small" variant="text" color="error" @click.stop="handleDelete(item)" />
                    <v-btn
                        v-if="item.deleted_at"
                        icon="mdi-restore"
                        size="small"
                        variant="text"
                        color="secondary"
                        @click.stop="handleRestore(item)"
                    />
                </template>

                <template #expanded-row="{ columns, item }">
                    <tr>
                        <td :colspan="columns.length">
                            <v-card variant="tonal" class="ma-3">
                                <v-card-title class="text-subtitle-1">{{ t('experiments.inputArguments') }}</v-card-title>
                                <v-card-text>
                                    <v-row v-if="Object.keys(item.input_arguments).length > 0">
                                        <v-col v-for="(spec, key) in item.input_arguments" :key="`${item.id}-${key}`" cols="12" md="6" lg="4">
                                            <v-sheet class="pa-3 border rounded">
                                                <div class="text-subtitle-2">{{ key }}</div>
                                                <div class="text-body-2">{{ t('experiments.argType') }}: {{ spec.type }}</div>
                                                <div class="text-body-2">{{ t('experiments.argValue') }}: {{ formatInputArgument(spec.value) }}</div>
                                                <div class="text-body-2">{{ t('experiments.argUnit') }}: {{ spec.unit || '-' }}</div>
                                            </v-sheet>
                                        </v-col>
                                    </v-row>
                                    <v-alert v-else type="info" variant="tonal">
                                        {{ t('experiments.noInputArguments') }}
                                    </v-alert>
                                </v-card-text>

                                <v-divider />

                                <v-card-title class="text-subtitle-1">{{ t('experiments.outputArguments') }}</v-card-title>
                                <v-card-text>
                                    <div class="d-flex flex-wrap ga-1" v-if="item.output_arguments.length > 0">
                                        <v-chip
                                            v-for="arg in item.output_arguments"
                                            :key="`${item.id}-output-${arg}`"
                                            size="small"
                                            color="primary"
                                            variant="outlined"
                                        >
                                            {{ arg }}
                                        </v-chip>
                                    </div>
                                    <v-alert v-else type="info" variant="tonal">
                                        {{ t('experiments.noOutputArguments') }}
                                    </v-alert>
                                </v-card-text>
                            </v-card>
                        </td>
                    </tr>
                </template>

                <template #no-data>
                    <v-alert type="info" variant="tonal" class="ma-4">
                        {{ t('experiments.noExperiments') }}
                    </v-alert>
                </template>
            </v-data-table>

            <v-alert v-if="error" type="error" variant="tonal" class="mt-4" closable>
                {{ error }}
            </v-alert>
        </v-container>
    </v-card>
</template>
