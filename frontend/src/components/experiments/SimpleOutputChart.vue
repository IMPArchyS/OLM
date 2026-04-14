<script setup lang="ts">
import Plotly from 'plotly.js-dist';
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

interface Props {
    outputHistory: Record<string, unknown>[];
    xKey?: string;
    title?: string;
    height?: number;
    emptyText?: string;
    fillContainer?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
    xKey: 'time',
    title: 'Output history',
    height: 220,
    emptyText: 'No output data available yet.',
    fillContainer: false,
});

const plotContainer = ref<HTMLElement | null>(null);
let resizeObserver: ResizeObserver | null = null;
let renderAnimationFrameId: number | null = null;
const emptyTicks = [0, 1, 2, 3, 4, 5];

const colors = ['#00897B', '#F4511E', '#1E88E5', '#D81B60', '#6D4C41', '#546E7A'];

const labels = computed(() => {
    return props.outputHistory.map((row, index) => {
        const value = row[props.xKey];
        if (typeof value === 'string' || typeof value === 'number') {
            return String(value);
        }

        return String(index + 1);
    });
});

const hasSeries = computed(() => {
    return numericKeys.value.length > 0;
});

const numericKeys = computed(() => {
    const keys = new Set<string>();

    for (const row of props.outputHistory) {
        for (const key of Object.keys(row)) {
            if (key !== props.xKey) {
                keys.add(key);
            }
        }
    }

    return Array.from(keys).filter((key) => {
        return props.outputHistory.some((row) => typeof row[key] === 'number');
    });
});

const traces = computed(() => {
    return numericKeys.value.map((key, index) => {
        return {
            type: 'scatter',
            mode: 'lines+markers',
            connectgaps: true,
            name: key,
            x: labels.value,
            y: props.outputHistory.map((row) => {
                const value = row[key];
                return typeof value === 'number' ? value : null;
            }),
            line: {
                color: colors[index % colors.length],
                width: 2,
                shape: 'spline',
            },
            marker: {
                size: 4,
            },
        };
    });
});

const renderTraces = computed(() => {
    if (hasSeries.value) {
        return traces.value;
    }

    return [
        {
            type: 'scatter',
            mode: 'lines',
            name: 'value',
            x: emptyTicks,
            y: emptyTicks.map(() => 0),
            showlegend: false,
            hoverinfo: 'skip',
            line: {
                color: 'rgba(0, 137, 123, 0.2)',
                width: 1,
                dash: 'dot',
            },
            opacity: 0,
        },
    ];
});

const layout = computed(() => {
    return {
        margin: {
            t: 8,
            r: 12,
            b: 40,
            l: 48,
        },
        hovermode: 'x unified',
        showlegend: hasSeries.value,
        legend: {
            orientation: 'h',
            y: -0.25,
        },
        xaxis: {
            title: {
                text: 'time',
            },
            type: hasSeries.value ? 'category' : 'linear',
            range: hasSeries.value ? undefined : [0, 5],
        },
        yaxis: {
            title: {
                text: 'values',
            },
            automargin: true,
            zeroline: false,
            range: hasSeries.value ? undefined : [0, 1],
        },
        annotations: hasSeries.value
            ? []
            : [
                  {
                      text: props.emptyText,
                      xref: 'paper',
                      yref: 'paper',
                      x: 0.5,
                      y: 0.5,
                      showarrow: false,
                      font: {
                          size: 13,
                          color: 'rgba(255,255,255,0.75)',
                      },
                  },
              ],
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
    };
});

const chartStyle = computed(() => {
    return {
        height: props.fillContainer ? '100%' : `${props.height}px`,
        minHeight: `${props.height}px`,
    };
});

const renderPlot = async () => {
    const container = plotContainer.value;
    if (!container) {
        return;
    }

    await nextTick();

    await Plotly.react(container, renderTraces.value, layout.value, {
        responsive: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    });
};

const scheduleRender = () => {
    if (renderAnimationFrameId !== null) {
        return;
    }

    renderAnimationFrameId = window.requestAnimationFrame(() => {
        renderAnimationFrameId = null;
        void renderPlot();
    });
};

watch(
    [() => props.outputHistory, () => props.xKey, hasSeries, numericKeys, labels],
    () => {
        scheduleRender();
    },
    { deep: true },
);

onMounted(() => {
    scheduleRender();

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
    if (renderAnimationFrameId !== null) {
        window.cancelAnimationFrame(renderAnimationFrameId);
        renderAnimationFrameId = null;
    }

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
    <v-card variant="outlined" class="simple-output-chart d-flex flex-column">
        <v-card-title class="text-subtitle-1">{{ title }}</v-card-title>
        <v-card-text class="chart-body">
            <div :style="chartStyle" class="chart-shell">
                <div ref="plotContainer" class="plot-container" />
            </div>
        </v-card-text>
    </v-card>
</template>

<style scoped>
.simple-output-chart {
    height: 100%;
}

.chart-body {
    display: flex;
    flex: 1 1 auto;
    min-height: 0;
}

.chart-shell {
    width: 100%;
}

.plot-container {
    width: 100%;
    height: 100%;
}
</style>
