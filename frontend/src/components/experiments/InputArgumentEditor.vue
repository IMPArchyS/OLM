<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { InputArgumentRow } from '@/utils/inputArguments';

const { t } = useI18n();

const rows = defineModel<InputArgumentRow[]>({ required: true });

const addRow = () => {
    rows.value.push({ key: '', type: 'number', value: 0, unit: '' });
};

const removeRow = (index: number) => {
    rows.value.splice(index, 1);
};
</script>

<template>
    <div>
        <div class="d-flex justify-space-between align-center mt-6 mb-2">
            <div class="text-subtitle-1">{{ t('experiments.inputArguments') }}</div>
            <v-btn color="info" variant="tonal" prepend-icon="mdi-plus" @click="addRow">
                {{ t('experiments.addInputArgument') }}
            </v-btn>
        </div>

        <v-row v-for="(row, index) in rows" :key="`input-arg-${index}`" class="mb-2">
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
                <v-btn icon="mdi-trash-can" color="error" variant="text" @click="removeRow(index)" />
            </v-col>
        </v-row>
    </div>
</template>
