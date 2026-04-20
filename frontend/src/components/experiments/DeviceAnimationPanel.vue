<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { useDeviceScene } from '@/composables/useDeviceScene';
import type { DeviceVisualConfig } from '@/types/api';

type OutputRow = Record<string, unknown>;

interface Props {
    visualConfig: DeviceVisualConfig | null;
    outputHistory: OutputRow[];
}

const props = defineProps<Props>();

const canvasRef = ref<HTMLCanvasElement | null>(null);
const sceneController = ref<ReturnType<typeof useDeviceScene> | null>(null);
const loadingModel = ref(false);
const loadError = ref('');
const processedIndex = ref(0);

const hasVisualConfig = computed(() => {
    return props.visualConfig !== null;
});

const hasFiniteNumber = (row: OutputRow, key: string): boolean => {
    const value = row[key];
    return typeof value === 'number' && Number.isFinite(value);
};

const blinkFromRow = (row: OutputRow) => {
    const controller = sceneController.value;
    if (!controller) {
        return;
    }

    if (hasFiniteNumber(row, 'sin_y')) {
        controller.triggerAnimation('led_transmitter', true);
    }

    if (hasFiniteNumber(row, 'cos_y')) {
        controller.triggerAnimation('led_receiver', true);
    }
};

const destroyScene = () => {
    sceneController.value?.dispose();
    sceneController.value = null;
};

const initScene = async () => {
    const canvas = canvasRef.value;
    const visualConfig = props.visualConfig;

    destroyScene();
    loadError.value = '';

    if (!canvas || !visualConfig) {
        loadingModel.value = false;
        return;
    }

    loadingModel.value = true;

    try {
        const controller = useDeviceScene(canvas, visualConfig);
        await controller.init();
        sceneController.value = controller;
        processedIndex.value = props.outputHistory.length;
    } catch (error: unknown) {
        destroyScene();
        loadError.value = error instanceof Error ? error.message : 'Failed to load 3D model.';
    } finally {
        loadingModel.value = false;
    }
};

watch(
    () => [canvasRef.value, props.visualConfig] as const,
    () => {
        void initScene();
    },
    { immediate: true },
);

watch(
    () => props.outputHistory,
    (rows) => {
        if (!sceneController.value) {
            return;
        }

        if (rows.length < processedIndex.value) {
            processedIndex.value = 0;
        }

        for (let index = processedIndex.value; index < rows.length; index += 1) {
            const row = rows[index];
            if (row) {
                blinkFromRow(row);
            }
        }

        processedIndex.value = rows.length;
    },
    { deep: false },
);

onBeforeUnmount(() => {
    destroyScene();
});
</script>

<template>
    <div class="device-animation-panel">
        <v-alert v-if="!hasVisualConfig" type="info" variant="tonal" class="mb-0"> No device visualization available for this device type. </v-alert>

        <v-alert v-else-if="loadError" type="error" variant="tonal" class="mb-0">
            {{ loadError }}
        </v-alert>

        <div v-else class="device-animation-canvas-shell">
            <canvas ref="canvasRef" class="device-animation-canvas" />
            <div v-if="loadingModel" class="device-animation-overlay">
                <v-progress-circular color="info" indeterminate size="36" />
                <span class="text-caption mt-2">Loading 3D model...</span>
            </div>
        </div>
    </div>
</template>

<style scoped>
.device-animation-panel {
    width: 100%;
    height: 100%;
    min-height: 260px;
}

.device-animation-canvas-shell {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 260px;
    overscroll-behavior: contain;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
    background: radial-gradient(circle at 30% 20%, rgba(var(--v-theme-info), 0.16), rgba(var(--v-theme-surface), 1));
}

.device-animation-canvas {
    width: 100%;
    height: 100%;
    display: block;
    touch-action: none;
}

.device-animation-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: rgba(var(--v-theme-surface), 0.74);
}
</style>
