<template>
    <div>
        <v-row class="mb-3">
            <v-col cols="3">
                <v-text-field
                    v-model="localArgument.name"
                    :label="$t('schemas.columns.argument.name')"
                    variant="outlined"
                    density="compact"
                    @update:model-value="emitChange"
                />
            </v-col>
            <v-col cols="3">
                <v-text-field
                    v-model="localArgument.label"
                    :label="$t('schemas.columns.argument.label')"
                    variant="outlined"
                    density="compact"
                    @update:model-value="emitChange"
                />
            </v-col>
            <v-col cols="3">
                <v-text-field
                    v-model="localArgument.default_value"
                    :label="$t('schemas.columns.argument.default_value')"
                    variant="outlined"
                    density="compact"
                    @update:model-value="handleDefaultValueChange"
                />
            </v-col>
            <v-col cols="3" class="d-flex align-center ga-2">
                <v-text-field
                    v-model.number="localArgument.row"
                    :label="$t('schemas.columns.argument.row')"
                    type="number"
                    variant="outlined"
                    density="compact"
                    class="grow"
                    @update:model-value="emitChange"
                />
                <v-text-field
                    v-model.number="localArgument.order"
                    :label="$t('schemas.columns.argument.order')"
                    type="number"
                    variant="outlined"
                    density="compact"
                    class="grow"
                    @update:model-value="emitChange"
                />
                <v-btn color="error" icon size="small" @click="$emit('delete')">
                    <v-icon>mdi-delete</v-icon>
                </v-btn>
            </v-col>
        </v-row>

        <v-row v-if="localArgument.options && localArgument.options.length > 0" class="mb-3">
            <v-col cols="12" offset-md="2" md="8">
                <h6 class="text-center mb-3">{{ $t('schemas.options') }}</h6>
                <SchemaFormOptions
                    v-for="(option, index) in localArgument.options"
                    :key="index"
                    :option="option"
                    :output-values="outputValues"
                    @change="handleOptionChange($event, index)"
                    @delete="handleDeleteOption(index)"
                />
                <div class="text-center mt-3">
                    <v-btn color="primary" prepend-icon="mdi-plus" @click="handleAddOption">
                        {{ $t('schemas.add_option') }}
                    </v-btn>
                </div>
            </v-col>
        </v-row>
        <v-row v-else class="mb-3">
            <v-col cols="12" offset-md="2" md="8">
                <div class="text-center">
                    <v-btn color="primary" prepend-icon="mdi-plus" @click="handleAddOption">
                        {{ $t('schemas.add_option') }}
                    </v-btn>
                </div>
            </v-col>
        </v-row>
    </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { ArgumentInput, OptionInput } from '@/types/api.ts';
import SchemaFormOptions from './SchemaFormOptions.vue';

interface Props {
    argument: ArgumentInput;
    outputValues?: string[];
}

const props = defineProps<Props>();
const emit = defineEmits<{
    change: [argument: ArgumentInput];
    delete: [];
}>();

const localArgument = ref<ArgumentInput>({ ...props.argument });

watch(
    () => props.argument,
    (newVal) => {
        localArgument.value = { ...newVal };
    },
);

const handleDefaultValueChange = (value: string | null) => {
    if (value !== null) {
        localArgument.value.default_value = value.replace(/[^0-9\,.\]\[\s]/g, '');
    }
    emitChange();
};

const handleAddOption = () => {
    const updated = { ...localArgument.value };
    if (!updated.options) {
        updated.options = [];
    }
    updated.options = [
        ...updated.options,
        {
            name: '',
            value: '',
            output_value: '',
        },
    ];
    localArgument.value = updated;
    emit('change', updated);
};

const handleOptionChange = (option: OptionInput, index: number) => {
    if (!localArgument.value.options) return;
    const updated = { ...localArgument.value };
    updated.options = [...localArgument.value.options];
    updated.options[index] = option;
    localArgument.value = updated;
    emit('change', updated);
};

const handleDeleteOption = (index: number) => {
    if (!localArgument.value.options) return;
    const updated = { ...localArgument.value };
    updated.options = [...localArgument.value.options];
    updated.options.splice(index, 1);
    localArgument.value = updated;
    emit('change', updated);
};

const emitChange = () => {
    emit('change', { ...localArgument.value });
};
</script>
