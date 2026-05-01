<script setup lang="ts">
import type { Step } from '@/types/api';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

interface Props {
    enabled: boolean;
    startValue: number;
    steps: Step[];
    density: 'default' | 'comfortable' | 'compact';
}

const props = defineProps<Props>();

const emit = defineEmits<{
    'update:enabled': [v: boolean];
    'update:startValue': [v: number];
    add: [];
    remove: [index: number];
    'update-step': [index: number, field: 'duration' | 'value', value: number];
}>();
</script>

<template>
    <v-checkbox
        :model-value="props.enabled"
        :label="t('dashboard.enable_setpoints')"
        :density="props.density"
        class="setpoint-editor__checkbox"
        @update:model-value="(v) => emit('update:enabled', Boolean(v))"
    />

    <div v-if="props.enabled" class="setpoint-editor__box">
        <div class="setpoint-editor__list">
            <div class="setpoint-editor__item setpoint-editor__item--start">
                <v-number-input
                    :model-value="0"
                    :label="`${t('dashboard.setpoint_step_duration')} #0`"
                    variant="outlined"
                    :density="props.density"
                    disabled
                />
                <v-number-input
                    :model-value="props.startValue"
                    :label="t('dashboard.setpoint_start_value')"
                    variant="outlined"
                    :density="props.density"
                    @update:model-value="(v) => emit('update:startValue', Number(v ?? 0))"
                />
            </div>

            <div
                v-for="(step, index) in props.steps"
                :key="`setpoint-step-${index}`"
                class="setpoint-editor__item"
            >
                <v-number-input
                    :model-value="step.duration"
                    :label="`${t('dashboard.setpoint_step_duration')} #${index + 1}`"
                    :min="0"
                    variant="outlined"
                    :density="props.density"
                    @update:model-value="(v) => emit('update-step', index, 'duration', Number(v ?? 0))"
                />
                <v-number-input
                    :model-value="step.value"
                    :label="`${t('dashboard.setpoint_step_value')} #${index + 1}`"
                    variant="outlined"
                    :density="props.density"
                    @update:model-value="(v) => emit('update-step', index, 'value', Number(v ?? 0))"
                />
                <div class="setpoint-editor__item-action">
                    <v-btn
                        color="error"
                        variant="text"
                        icon="mdi-trash-can"
                        :disabled="props.steps.length <= 1"
                        @click="emit('remove', index)"
                    />
                </div>
            </div>
        </div>

        <div class="setpoint-editor__action">
            <v-btn color="info" prepend-icon="mdi-plus" @click="emit('add')">
                {{ t('dashboard.add_setpoint_step') }}
            </v-btn>
        </div>
    </div>
</template>

<style scoped>
.setpoint-editor__checkbox {
    margin-top: -4px;
}

.setpoint-editor__box {
    display: flex;
    flex-direction: column;
    gap: 12px;
    border-radius: 10px;
    padding: 12px;
}

.setpoint-editor__list {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
}

.setpoint-editor__item {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
    align-items: start;
    padding: 10px;
    border-radius: 8px;
    border: 1px solid rgba(128, 128, 128, 0.3);
}

.setpoint-editor__item--start {
    border-style: dashed;
}

.setpoint-editor__item-action {
    display: flex;
    justify-content: flex-end;
}

.setpoint-editor__action {
    display: flex;
    justify-content: flex-start;
}
</style>
