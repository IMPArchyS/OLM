import { ref, computed, watch } from 'vue';
import type { ComputedRef } from 'vue';
import type { Experiment, Step } from '@/types/api';
import type { ExperimentFormData } from '@/types/forms';

export function useSetpointEditor(selectedExperiment: ComputedRef<Experiment | null>) {
    const useSetpoints = ref<boolean>(false);
    const setpointStartValue = ref<number>(0);
    const setpointSteps = ref<Step[]>([]);

    watch(
        selectedExperiment,
        () => {
            useSetpoints.value = false;
            setpointStartValue.value = 0;
            setpointSteps.value = [];
        },
        { immediate: true },
    );

    watch(useSetpoints, (enabled) => {
        if (!enabled) {
            setpointStartValue.value = 0;
            setpointSteps.value = [];
            return;
        }
        if (setpointSteps.value.length === 0) {
            setpointSteps.value = [{ duration: 0, value: 0 }];
        }
    });

    const addSetpointStep = () => {
        if (!selectedExperiment.value || !useSetpoints.value) return;
        setpointSteps.value.push({ duration: 0, value: 0 });
    };

    const removeSetpointStep = (index: number) => {
        if (setpointSteps.value.length <= 1) return;
        setpointSteps.value.splice(index, 1);
    };

    const setpointChanges = computed<ExperimentFormData['setpoint_changes']>(() => {
        if (!useSetpoints.value || setpointSteps.value.length === 0) {
            return {} as Record<string, never>;
        }
        return {
            start_value: setpointStartValue.value,
            steps: setpointSteps.value,
        };
    });

    return {
        useSetpoints,
        setpointStartValue,
        setpointSteps,
        addSetpointStep,
        removeSetpointStep,
        setpointChanges,
    };
}
