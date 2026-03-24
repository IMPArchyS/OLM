<script setup lang="ts">
import { computed } from 'vue';
import { Line } from 'vue-chartjs';
import { CategoryScale, Chart as ChartJS, Filler, Legend, LineElement, LinearScale, PointElement, Tooltip } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

interface Props {
    outputHistory: Record<string, unknown>[];
    xKey?: string;
    title?: string;
}

const props = withDefaults(defineProps<Props>(), {
    xKey: 'time',
    title: 'Output history',
});

const colorPalette = ['#00796B', '#F57C00', '#1976D2', '#C2185B', '#5D4037', '#455A64'];

const hasRows = computed(() => props.outputHistory.length > 0);

const labels = computed(() => {
    return props.outputHistory.map((row, index) => {
        const value = row[props.xKey];
        if (typeof value === 'number' || typeof value === 'string') {
            return String(value);
        }
        return String(index + 1);
    });
});

const seriesKeys = computed(() => {
    const allKeys = new Set<string>();

    for (const row of props.outputHistory) {
        for (const key of Object.keys(row)) {
            if (key !== props.xKey) {
                allKeys.add(key);
            }
        }
    }

    return Array.from(allKeys).filter((key) => {
        return props.outputHistory.some((row) => typeof row[key] === 'number');
    });
});

const chartData = computed(() => {
    return {
        labels: labels.value,
        datasets: seriesKeys.value.map((key, index) => ({
            label: key,
            data: props.outputHistory.map((row) => {
                const value = row[key];
                return typeof value === 'number' ? value : null;
            }),
            borderColor: colorPalette[index % colorPalette.length],
            backgroundColor: `${colorPalette[index % colorPalette.length]}22`,
            tension: 0.3,
            pointRadius: 2,
            pointHoverRadius: 4,
            fill: false,
            spanGaps: true,
        })),
    };
});

const chartOptions = computed(() => {
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index' as const,
            intersect: false,
        },
        plugins: {
            legend: {
                position: 'bottom' as const,
            },
            tooltip: {
                enabled: true,
            },
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: props.xKey,
                },
            },
            y: {
                beginAtZero: false,
            },
        },
    };
});
</script>

<template>
    <v-card variant="tonal">
        <v-card-title class="text-subtitle-1">{{ title }}</v-card-title>
        <v-card-text>
            <div v-if="!hasRows" class="text-medium-emphasis">No output data available.</div>
            <div v-else-if="seriesKeys.length === 0" class="text-medium-emphasis">Output data has no numeric fields to plot.</div>
            <div v-else style="height: 280px">
                <Line :data="chartData" :options="chartOptions" />
            </div>
        </v-card-text>
    </v-card>
</template>
