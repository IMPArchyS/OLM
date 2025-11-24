<template>
    <v-row class="mb-3">
        <v-col cols="1"></v-col>
        <v-col cols="3">
            <v-text-field
                v-model="localOption.name"
                :label="$t('schemas.columns.argument.option.name')"
                variant="outlined"
                density="compact"
                required
                @update:model-value="emitChange"
            />
        </v-col>
        <v-col cols="3">
            <v-text-field
                v-model="localOption.value"
                :label="$t('schemas.columns.argument.option.value')"
                variant="outlined"
                density="compact"
                required
                @update:model-value="handleValueChange"
            />
        </v-col>
        <v-col cols="3">
            <v-select
                v-model="localOption.output_value"
                :items="outputValueItems"
                :label="$t('schemas.columns.argument.option.output_value')"
                variant="outlined"
                density="compact"
                @update:model-value="emitChange"
            />
        </v-col>
        <v-col cols="2" class="d-flex align-center">
            <v-btn color="error" icon size="small" @click="$emit('delete')">
                <v-icon>mdi-delete</v-icon>
            </v-btn>
        </v-col>
    </v-row>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { OptionInput } from '@/types/api.ts'

interface Props {
    option: OptionInput
    outputValues?: string[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
    change: [option: OptionInput]
    delete: []
}>()

const localOption = ref<OptionInput>({ ...props.option })

watch(
    () => props.option,
    (newVal) => {
        localOption.value = { ...newVal }
    },
    { deep: true },
)

const outputValueItems = computed(() => {
    if (!props.outputValues) return []
    return [
        { title: '', value: '' },
        ...props.outputValues.map((val) => ({
            title: `${val}`,
            value: val,
        })),
    ]
})

const handleValueChange = (value: string) => {
    // Only allow numbers, commas, periods, brackets, and spaces
    localOption.value.value = value.replace(/[^0-9\,.\]\[\s]/g, '')
    emitChange()
}

const emitChange = () => {
    emit('change', { ...localOption.value })
}
</script>
