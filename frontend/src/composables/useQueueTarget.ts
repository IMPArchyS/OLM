import { computed, ref, watch, type Ref } from 'vue';
import type { Device, Experiment } from '@/types/api';

type QueueTargetMode = 'same-as-last' | 'any-compatible' | 'pick-device';

export function useQueueTarget(selectedExperiment: Ref<Experiment | null>, lastUsedDeviceId: Ref<number | null>) {
    const queueTargetMode = ref<QueueTargetMode>('any-compatible');
    const manualDeviceId = ref<number | null>(null);

    const compatibleDevices = computed<Device[]>(() => (selectedExperiment.value?.devices ?? []).filter((device) => !device.deleted_at));

    const resolvedDeviceId = computed<number | null>(() => {
        if (queueTargetMode.value === 'same-as-last') return lastUsedDeviceId.value;
        if (queueTargetMode.value === 'pick-device') return manualDeviceId.value;
        return null;
    });

    watch(
        () => selectedExperiment.value?.id ?? null,
        () => {
            manualDeviceId.value = null;
            queueTargetMode.value = 'any-compatible';
        },
    );

    watch(lastUsedDeviceId, (newId) => {
        if (newId !== null && queueTargetMode.value === 'any-compatible') {
            queueTargetMode.value = 'same-as-last';
        }
    });

    watch(queueTargetMode, (mode) => {
        if (mode !== 'pick-device') manualDeviceId.value = null;
    });

    return { queueTargetMode, manualDeviceId, resolvedDeviceId, compatibleDevices };
}
