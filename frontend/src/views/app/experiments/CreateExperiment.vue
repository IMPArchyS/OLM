<script lang="ts" setup>
import { useDevices } from '@/composables/useDevices';
import { useExperiments } from '@/composables/useExperiments';
import router from '@/router';
import { useToastStore } from '@/stores/toast';
import type { CreateExperimentForm } from '@/types/forms';
import { buildInputArguments } from '@/utils/inputArguments';
import type { InputArgumentRow } from '@/utils/inputArguments';
import InputArgumentEditor from '@/components/experiments/InputArgumentEditor.vue';
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const toast = useToastStore();
const { devices, fetchDevices } = useDevices();
const { softwares, defaultCommands, fetchSoftwares, createExperiment } = useExperiments();

const formRef = ref();
const valid = ref(false);
const triedSubmit = ref(false);
const selectedDeviceIds = ref<number[]>([]);
const selectedSoftwareId = ref<number | null>(null);
const inputArgumentRows = ref<InputArgumentRow[]>([{ key: '', type: 'string', value: '', unit: '' }]);
const outputArguments = ref<string[]>([]);

const availableDevices = computed(() => {
    if (!selectedSoftwareId.value) {
        return [];
    }

    return devices.value.filter((device) => !device.deleted_at && !!device.softwares?.some((software) => software.id === selectedSoftwareId.value));
});

watch(selectedSoftwareId, () => {
    selectedDeviceIds.value = [];
});

const requiredRule = (value: unknown) => !!value || t('validation.required');
const deviceRules = computed(() => [
    (value: number[] | null | undefined) => {
        if (!selectedSoftwareId.value) {
            return true;
        }

        if (!triedSubmit.value) {
            return true;
        }

        const selectedCount = Array.isArray(value) ? value.length : 0;
        return selectedCount > 0 || t('validation.required');
    },
]);

const handleCreate = async () => {
    triedSubmit.value = true;
    await nextTick();
    const validationResult = await formRef.value?.validate();
    valid.value = !!validationResult?.valid;

    if (!valid.value) {
        toast.error(t('validation.formInvalid'));
        return;
    }

    const buildResult = buildInputArguments(inputArgumentRows.value);
    if (buildResult.error) {
        const errorMessages = {
            duplicate: t('experiments.inputArgDuplicate'),
            invalid_number: t('experiments.inputArgInvalidNumber'),
        };
        toast.error(errorMessages[buildResult.error]);
        return;
    }

    const payload: CreateExperimentForm = {
        commands: defaultCommands,
        input_arguments: buildResult.data,
        output_arguments: outputArguments.value.filter((item) => item.trim().length > 0),
        device_ids: selectedDeviceIds.value,
        software_id: Number(selectedSoftwareId.value),
    };

    const result = await createExperiment(payload);
    if (result.success) {
        toast.success(result.message || t('common.success'));
        await router.push({ name: 'experiments' });
    } else {
        toast.error(result.message || t('common.error'));
    }
};

const handleCancel = () => {
    router.push({ name: 'experiments' });
};

onMounted(async () => {
    const [devicesResult, softwaresResult] = await Promise.all([fetchDevices(), fetchSoftwares()]);

    if (!devicesResult.success) {
        toast.error(devicesResult.message || t('common.error'));
    }

    if (!softwaresResult.success) {
        toast.error(softwaresResult.message || t('common.error'));
    }
});
</script>

<template>
    <v-card elevation="4">
        <v-card-title class="bg-card-title">
            <v-icon icon="mdi-plus-box-outline" class="mr-2" />
            <span>{{ t('actions.create') }}</span>
        </v-card-title>

        <v-divider />

        <v-card-text>
            <v-form ref="formRef" v-model="valid">
                <v-select
                    v-model="selectedSoftwareId"
                    :items="softwares"
                    item-title="name"
                    item-value="id"
                    :label="t('experiments.software')"
                    :rules="[requiredRule]"
                    variant="outlined"
                    density="comfortable"
                    required
                />

                <v-select
                    v-model="selectedDeviceIds"
                    :items="availableDevices"
                    item-title="name"
                    item-value="id"
                    :label="t('experiments.devices')"
                    :rules="deviceRules"
                    :hint="
                        selectedSoftwareId
                            ? availableDevices.length > 0
                                ? ''
                                : t('experiments.noCompatibleDevices')
                            : t('experiments.pickSoftwareFirst')
                    "
                    persistent-hint
                    variant="outlined"
                    density="comfortable"
                    multiple
                    chips
                    :disabled="!selectedSoftwareId"
                    required
                />

                <div class="mb-4">
                    <div class="text-subtitle-1 mb-2">{{ t('experiments.commands') }}</div>
                    <div class="d-flex flex-wrap ga-2">
                        <v-chip v-for="command in defaultCommands" :key="command" color="info" variant="tonal">
                            {{ command }}
                        </v-chip>
                    </div>
                </div>

                <v-combobox
                    v-model="outputArguments"
                    :label="t('experiments.outputArguments')"
                    :hint="t('experiments.outputArgumentsHint')"
                    persistent-hint
                    variant="outlined"
                    density="comfortable"
                    multiple
                    chips
                    closable-chips
                />

                <InputArgumentEditor v-model="inputArgumentRows" />
            </v-form>
        </v-card-text>

        <v-card-actions>
            <v-spacer />
            <v-btn prepend-icon="mdi-close" color="grey" variant="outlined" @click="handleCancel">
                {{ t('actions.cancel') }}
            </v-btn>
            <v-btn prepend-icon="mdi-plus" color="primary" variant="elevated" @click="handleCreate">
                {{ t('actions.create') }}
            </v-btn>
        </v-card-actions>
    </v-card>
</template>
