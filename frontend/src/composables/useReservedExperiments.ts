import type { ReservedExperiment } from '@/types/api';
import { ref } from 'vue';

export function useReservedExperiments() {
    const reservedExperiments = ref<ReservedExperiment[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);

    return {
        reservedExperiments,
        loading,
        error,
    };
}
