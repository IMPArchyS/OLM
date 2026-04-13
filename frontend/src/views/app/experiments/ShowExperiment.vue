<script lang="ts" setup>
import { useExperiments } from '@/composables/useExperiments';
import { useDevices } from '@/composables/useDevices';
import router from '@/router';
import { useToastStore } from '@/stores/toast';
import type { Experiment } from '@/types/api';
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';

const { t } = useI18n();
const toast = useToastStore();
const route = useRoute();
const experimentId = Number(route.params.id);

const { getExperimentById } = useExperiments();
const { devices, fetchDevices } = useDevices();

const loading = ref(false);
const experiment = ref<Experiment | null>(null);
const deletedDeviceIdSet = computed(() => new Set(devices.value.filter((device) => !!device.deleted_at).map((device) => device.id)));
const hasDeletedLinkedDevice = computed(() => {
    if (!experiment.value) {
        return false;
    }

    return experiment.value.devices.some((device) => !!device.deleted_at || deletedDeviceIdSet.value.has(device.id));
});

const handleBack = () => {
    router.push({ name: 'experiments' });
};

const handleEdit = () => {
    router.push({ name: 'experiments-edit', params: { id: experimentId } });
};

const loadExperiment = async () => {
    loading.value = true;

    try {
        const [currentExperiment, devicesResult] = await Promise.all([getExperimentById(experimentId), fetchDevices()]);

        if (!devicesResult.success) {
            toast.error(devicesResult.message || t('common.error'));
        }

        if (!currentExperiment) {
            toast.info(t('experiments.notFound'));
            router.back();
            return;
        }

        experiment.value = currentExperiment;
    } catch (e) {
        toast.error(t('common.errorLoadingData'));
        router.back();
    } finally {
        loading.value = false;
    }
};

onMounted(async () => {
    await loadExperiment();
});
</script>

<template>
    <v-container fluid>
        <v-card :loading="loading">
            <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
                <span class="text-h5">{{ t('experiments.viewExperiment') }}</span>
            </v-card-title>

            <v-divider />

            <v-card-text v-if="!loading && experiment">
                <v-alert v-if="hasDeletedLinkedDevice" type="warning" variant="tonal" class="mb-4">
                    {{ t('experiments.deletedLinkedDeviceWarning') }}
                </v-alert>

                <v-text-field
                    :model-value="experiment.software?.name || t('experiments.noSoftware')"
                    :label="t('experiments.software')"
                    variant="outlined"
                    density="comfortable"
                    readonly
                />

                <div class="mb-4">
                    <div class="text-subtitle-1 mb-2">{{ t('experiments.commands') }}</div>
                    <div class="d-flex flex-wrap ga-2">
                        <v-chip v-for="command in experiment.commands" :key="`${experiment.id}-${command}`" color="info" variant="tonal">
                            {{ command }}
                        </v-chip>
                    </div>
                </div>

                <div class="mb-4">
                    <div class="text-subtitle-1 mb-2">{{ t('experiments.devices') }}</div>
                    <div class="d-flex flex-wrap ga-2">
                        <v-chip v-for="device in experiment.devices" :key="device.id" color="primary" variant="outlined">
                            {{ device.name }}
                        </v-chip>
                    </div>
                </div>

                <div class="mb-4">
                    <div class="text-subtitle-1 mb-2">{{ t('experiments.outputArguments') }}</div>
                    <div class="d-flex flex-wrap ga-2" v-if="experiment.output_arguments.length > 0">
                        <v-chip v-for="arg in experiment.output_arguments" :key="`${experiment.id}-out-${arg}`" color="primary" variant="outlined">
                            {{ arg }}
                        </v-chip>
                    </div>
                    <v-alert v-else type="info" variant="tonal">
                        {{ t('experiments.noOutputArguments') }}
                    </v-alert>
                </div>

                <div class="mb-2">
                    <div class="text-subtitle-1 mb-2">{{ t('experiments.inputArguments') }}</div>
                    <v-row v-if="Object.keys(experiment.input_arguments).length > 0">
                        <v-col v-for="(spec, key) in experiment.input_arguments" :key="`${experiment.id}-in-${key}`" cols="12" md="6" lg="4">
                            <v-sheet class="pa-3 border rounded">
                                <div class="text-subtitle-2">{{ key }}</div>
                                <div class="text-body-2">{{ t('experiments.argType') }}: {{ spec.type }}</div>
                                <div class="text-body-2">{{ t('experiments.argValue') }}: {{ spec.value }}</div>
                                <div class="text-body-2">{{ t('experiments.argUnit') }}: {{ spec.unit || '-' }}</div>
                            </v-sheet>
                        </v-col>
                    </v-row>
                    <v-alert v-else type="info" variant="tonal">
                        {{ t('experiments.noInputArguments') }}
                    </v-alert>
                </div>
            </v-card-text>

            <v-card-actions v-if="!loading && experiment">
                <v-spacer />
                <v-btn color="grey" variant="text" @click="handleBack">
                    {{ t('actions.back') }}
                </v-btn>
                <v-btn color="primary" variant="elevated" @click="handleEdit">
                    {{ t('actions.edit') }}
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-container>
</template>
