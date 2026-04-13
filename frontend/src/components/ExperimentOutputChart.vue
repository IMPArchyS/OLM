<script setup lang="ts">
import Plotly from 'plotly.js';
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

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
const plotContainer = ref<HTMLElement | null>(null);

let resizeObserver: ResizeObserver | null = null;

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

const plotData = computed(() => {
    return {
        x: labels.value,
        traces: seriesKeys.value.map((key, index) => ({
            name: key,
            y: props.outputHistory.map((row) => {
                const value = row[key];
                return typeof value === 'number' ? value : null;
            }),
            type: 'scatter',
            mode: 'lines+markers',
            connectgaps: true,
            line: {
                color: colorPalette[index % colorPalette.length],
                width: 2,
                shape: 'spline',
            },
            marker: {
                size: 5,
            },
        })),
    };
});

const plotLayout = computed(() => {
    return {
        margin: {
            t: 16,
            r: 20,
            b: 48,
            l: 56,
        },
        hovermode: 'x unified',
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.2,
        },
        xaxis: {
            title: {
                text: props.xKey,
            },
            type: 'category',
        },
        yaxis: {
            automargin: true,
            zeroline: false,
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
    };
});

const renderPlot = async () => {
    const container = plotContainer.value;
    if (!container) {
        return;
    }

    if (!hasRows.value || seriesKeys.value.length === 0) {
        Plotly.purge(container);
        return;
    }

    await nextTick();

    await Plotly.react(
        container,
        plotData.value.traces.map((trace) => ({
            ...trace,
            x: plotData.value.x,
        })),
        plotLayout.value,
        {
            responsive: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            toImageButtonOptions: {
                format: 'png',
                filename: 'output-history',
            },
        },
    );
};

watch(
    [() => props.outputHistory, () => props.xKey, hasRows, seriesKeys, labels],
    () => {
        void renderPlot();
    },
    { deep: true },
);

onMounted(() => {
    void renderPlot();

    if (plotContainer.value) {
        resizeObserver = new ResizeObserver(() => {
            if (plotContainer.value) {
                Plotly.Plots.resize(plotContainer.value);
            }
        });

        resizeObserver.observe(plotContainer.value);
    }
});

onBeforeUnmount(() => {
    if (resizeObserver) {
        resizeObserver.disconnect();
        resizeObserver = null;
    }

    if (plotContainer.value) {
        Plotly.purge(plotContainer.value);
    }
});
</script>

<template>
    <v-card variant="tonal">
        <v-card-title class="text-subtitle-1">{{ title }}</v-card-title>
        <v-card-text>
            <div v-if="!hasRows" class="text-medium-emphasis">No output data available.</div>
            <div v-else-if="seriesKeys.length === 0" class="text-medium-emphasis">Output data has no numeric fields to plot.</div>
            <div v-else style="height: 280px">
                <div ref="plotContainer" style="height: 100%; width: 100%" />
            </div>
        </v-card-text>
    </v-card>
</template>
