declare module 'plotly.js' {
    type PlotlyTrace = Record<string, unknown>;
    type PlotlyLayout = Record<string, unknown>;
    type PlotlyConfig = Record<string, unknown>;

    interface PlotlyStatic {
        react: (root: HTMLElement, data: PlotlyTrace[], layout?: PlotlyLayout, config?: PlotlyConfig) => Promise<unknown>;
        purge: (root: HTMLElement) => void;
        Plots: {
            resize: (root: HTMLElement) => void;
        };
    }

    const Plotly: PlotlyStatic;
    export default Plotly;
}
