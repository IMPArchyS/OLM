<template>
    <div>
        <h5 class="text-center mt-6 mb-4">{{ $t('schemas.arguments') }}</h5>

        <template v-for="(argument, index) in localArguments" :key="index">
            <SchemaFormArgumentsRow
                :argument="argument"
                :output-values="outputValues"
                @change="handleArgumentChange($event, index)"
                @delete="handleDeleteArgument(index)"
            />
            <v-divider class="my-4" />
        </template>

        <div class="text-center mt-4">
            <v-btn color="primary" prepend-icon="mdi-plus" @click="handleAddArgument">
                {{ $t('schemas.add_argument') }}
            </v-btn>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { ArgumentInput } from '@/types/api.ts';
import SchemaFormArgumentsRow from './SchemaFormArgumentsRow.vue';

interface Props {
    schemaArguments?: ArgumentInput[];
    outputValues?: string[];
}

const props = withDefaults(defineProps<Props>(), {
    schemaArguments: () => [],
});

const emit = defineEmits<{
    change: [arguments: ArgumentInput[]];
}>();

const localArguments = ref<ArgumentInput[]>([...props.schemaArguments]);

watch(
    () => props.schemaArguments,
    (newVal) => {
        localArguments.value = [...newVal];
    },
);

const handleAddArgument = () => {
    const updated = [
        ...localArguments.value,
        {
            name: '',
            label: '',
            default_value: '',
            row: 1,
            order: 1,
            options: [],
        },
    ];
    localArguments.value = updated;
    emit('change', updated);
};

const handleArgumentChange = (argument: ArgumentInput, index: number) => {
    const updated = [...localArguments.value];
    updated[index] = argument;
    localArguments.value = updated;
    emit('change', updated);
};

const handleDeleteArgument = (index: number) => {
    const updated = [...localArguments.value];
    updated.splice(index, 1);
    localArguments.value = updated;
    emit('change', updated);
};
</script>
