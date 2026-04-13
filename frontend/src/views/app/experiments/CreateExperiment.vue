<script lang="ts" setup>
import { useDevices } from '@/composables/useDevices';
import { useExperiments } from '@/composables/useExperiments';
import router from '@/router';
import { useToastStore } from '@/stores/toast';
import type { InputArgSpec } from '@/types/api';
import type { CreateExperimentForm } from '@/types/forms';
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

interface InputArgumentRow {
    key: string;
    type: InputArgSpec['type'];
    value: number | string;
    unit: string;
}

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

const addInputArgument = () => {
    inputArgumentRows.value.push({
        key: '',
        type: 'number',
        value: 0,
        unit: '',
    });
};

const removeInputArgument = (index: number) => {
    inputArgumentRows.value.splice(index, 1);
};

const buildInputArguments = (): Record<string, InputArgSpec> | null => {
    const inputArguments: Record<string, InputArgSpec> = {};

    for (const row of inputArgumentRows.value) {
        const key = row.key.trim();

        if (!key) {
            continue;
        }

        if (inputArguments[key]) {
            toast.error(t('experiments.inputArgDuplicate'));
            return null;
        }

        if (row.type === 'number') {
            const numericValue = Number(row.value);
            if (Number.isNaN(numericValue)) {
                toast.error(t('experiments.inputArgInvalidNumber'));
                return null;
            }

            inputArguments[key] = {
                type: row.type,
                value: numericValue,
                unit: row.unit.trim(),
            };
            continue;
        }

        inputArguments[key] = {
            type: row.type,
            value: String(row.value ?? ''),
            unit: row.unit.trim(),
        };
    }

    return inputArguments;
};

const handleCreate = async () => {
    triedSubmit.value = true;
    await nextTick();
    const validationResult = await formRef.value?.validate();
    valid.value = !!validationResult?.valid;

    if (!valid.value) {
        toast.error(t('validation.formInvalid'));
        return;
    }

    const inputArguments = buildInputArguments();
    if (inputArguments === null) {
        return;
    }

    const payload: CreateExperimentForm = {
        commands: defaultCommands,
        input_arguments: inputArguments,
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
    <v-container fluid>
        <v-card>
            <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
                <span class="text-h5">{{ t('experiments.addExperiment') }}</span>
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

                    <div class="d-flex justify-space-between align-center mt-6 mb-2">
                        <div class="text-subtitle-1">{{ t('experiments.inputArguments') }}</div>
                        <v-btn color="info" variant="tonal" prepend-icon="mdi-plus" @click="addInputArgument">
                            {{ t('experiments.addInputArgument') }}
                        </v-btn>
                    </div>

                    <v-row v-for="(row, index) in inputArgumentRows" :key="`input-arg-${index}`" class="mb-2">
                        <v-col cols="12" md="3">
                            <v-text-field v-model="row.key" :label="t('experiments.argName')" variant="outlined" density="comfortable" required />
                        </v-col>
                        <v-col cols="12" md="2">
                            <v-select
                                v-model="row.type"
                                :items="['number', 'string']"
                                :label="t('experiments.argType')"
                                variant="outlined"
                                density="comfortable"
                            />
                        </v-col>
                        <v-col cols="12" md="3">
                            <v-text-field
                                v-if="row.type === 'number'"
                                v-model.number="row.value"
                                type="number"
                                :label="t('experiments.argValue')"
                                variant="outlined"
                                density="comfortable"
                            />
                            <v-text-field v-else v-model="row.value" :label="t('experiments.argValue')" variant="outlined" density="comfortable" />
                        </v-col>
                        <v-col cols="12" md="3">
                            <v-text-field v-model="row.unit" :label="t('experiments.argUnit')" variant="outlined" density="comfortable" />
                        </v-col>
                        <v-col cols="12" md="1" class="d-flex justify-end align-center">
                            <v-btn icon="mdi-delete" color="error" variant="text" @click="removeInputArgument(index)" />
                        </v-col>
                    </v-row>
                </v-form>
            </v-card-text>

            <v-card-actions>
                <v-spacer />
                <v-btn color="grey" variant="text" @click="handleCancel">
                    {{ t('actions.cancel') }}
                </v-btn>
                <v-btn color="primary" variant="elevated" @click="handleCreate">
                    {{ t('actions.create') }}
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-container>
</template>
