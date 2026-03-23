import type { ExperimentLog } from '@/types/api';
import { ref } from 'vue';

export function useReservedExperiments() {
    const reservedExperiments = ref<ExperimentLog[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);

    return {
        reservedExperiments,
        loading,
        error,
    };
}
