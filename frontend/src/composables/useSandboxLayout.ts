import { ref, computed, watch } from 'vue';
import type { Layout } from 'grid-layout-plus';

export type SandboxPanelId = 'control' | 'chart' | 'camera' | 'animation';

export type PanelMeta = {
    title: string;
    icon: string;
    minW: number;
    minH: number;
    defaultW: number;
    defaultH: number;
    defaultX: number;
    defaultY: number;
};

const STORAGE_LAYOUT_KEY = 'olm:sandbox:grid-layout:v2';
const STORAGE_VISIBILITY_KEY = 'olm:sandbox:grid-visibility:v1';
const COLLAPSED_H = 6;

export function useSandboxLayout(
    panelIds: SandboxPanelId[],
    defaultPanelMeta: Record<SandboxPanelId, PanelMeta>,
) {
    const makeDefaultLayout = (): Layout =>
        panelIds.map((panelId) => {
            const meta = defaultPanelMeta[panelId];
            return { i: panelId, x: meta.defaultX, y: meta.defaultY, w: meta.defaultW, h: meta.defaultH, minW: meta.minW, minH: meta.minH };
        });

    const readStoredLayout = (): Layout => {
        const fallback = makeDefaultLayout();
        const raw = localStorage.getItem(STORAGE_LAYOUT_KEY);
        if (!raw) return fallback;
        try {
            const parsed = JSON.parse(raw) as Layout;
            if (!Array.isArray(parsed)) return fallback;
            return panelIds.map((panelId) => {
                const meta = defaultPanelMeta[panelId];
                const item = parsed.find((entry) => String(entry.i) === panelId);
                if (!item) {
                    return { i: panelId, x: meta.defaultX, y: meta.defaultY, w: meta.defaultW, h: meta.defaultH, minW: meta.minW, minH: meta.minH };
                }
                return {
                    i: panelId,
                    x: Number.isFinite(item.x) ? item.x : meta.defaultX,
                    y: Number.isFinite(item.y) ? item.y : meta.defaultY,
                    w: Math.max(meta.minW, Number.isFinite(item.w) ? item.w : meta.defaultW),
                    h: Math.max(meta.minH, Number.isFinite(item.h) ? item.h : meta.defaultH),
                    minW: meta.minW,
                    minH: meta.minH,
                };
            });
        } catch {
            return fallback;
        }
    };

    const readPanelVisibility = (): Record<SandboxPanelId, boolean> => {
        const fallback = Object.fromEntries(panelIds.map((id) => [id, true])) as Record<SandboxPanelId, boolean>;
        const raw = localStorage.getItem(STORAGE_VISIBILITY_KEY);
        if (!raw) return fallback;
        try {
            const parsed = JSON.parse(raw) as Partial<Record<SandboxPanelId, unknown>>;
            return Object.fromEntries(
                panelIds.map((id) => [id, parsed[id] === undefined ? true : Boolean(parsed[id])]),
            ) as Record<SandboxPanelId, boolean>;
        } catch {
            return fallback;
        }
    };

    const panelLayout = ref<Layout>(readStoredLayout());
    const panelVisibility = ref<Record<SandboxPanelId, boolean>>(readPanelVisibility());
    const collapsedPanels = ref<Record<SandboxPanelId, boolean>>(
        Object.fromEntries(panelIds.map((id) => [id, false])) as Record<SandboxPanelId, boolean>,
    );
    const savedHeights = ref<Record<SandboxPanelId, number>>(
        Object.fromEntries(panelIds.map((id) => [id, defaultPanelMeta[id].defaultH])) as Record<SandboxPanelId, number>,
    );

    const persistLayoutState = () => {
        localStorage.setItem(STORAGE_LAYOUT_KEY, JSON.stringify(panelLayout.value));
        localStorage.setItem(STORAGE_VISIBILITY_KEY, JSON.stringify(panelVisibility.value));
    };

    const visiblePanelLayout = computed<Layout>(() =>
        panelLayout.value.filter((entry) => panelVisibility.value[String(entry.i) as SandboxPanelId]),
    );

    const resetLayout = () => {
        panelVisibility.value = Object.fromEntries(panelIds.map((id) => [id, true])) as Record<SandboxPanelId, boolean>;
        collapsedPanels.value = Object.fromEntries(panelIds.map((id) => [id, false])) as Record<SandboxPanelId, boolean>;
        panelLayout.value = makeDefaultLayout();
    };

    const setPanelVisibility = (panelId: SandboxPanelId, visible: boolean) => {
        panelVisibility.value = { ...panelVisibility.value, [panelId]: visible };
    };

    const toggleCollapse = (panelId: SandboxPanelId) => {
        const isCollapsed = collapsedPanels.value[panelId];
        if (isCollapsed) {
            panelLayout.value = panelLayout.value.map((item) =>
                String(item.i) === panelId
                    ? { ...item, h: savedHeights.value[panelId] ?? defaultPanelMeta[panelId].defaultH, minH: defaultPanelMeta[panelId].minH }
                    : item,
            );
        } else {
            const current = panelLayout.value.find((item) => String(item.i) === panelId);
            if (current) savedHeights.value = { ...savedHeights.value, [panelId]: current.h };
            panelLayout.value = panelLayout.value.map((item) =>
                String(item.i) === panelId ? { ...item, h: COLLAPSED_H, minH: COLLAPSED_H } : item,
            );
        }
        collapsedPanels.value = { ...collapsedPanels.value, [panelId]: !isCollapsed };
    };

    const handleLayoutUpdate = (layout: Layout, isMobile: boolean) => {
        if (isMobile) return;
        const layoutById = new Map(layout.map((entry) => [String(entry.i), entry]));
        const merged = panelLayout.value.map((entry) => layoutById.get(String(entry.i)) ?? entry);
        panelLayout.value = panelIds.map((panelId) => {
            const meta = defaultPanelMeta[panelId];
            const item = merged.find((entry) => String(entry.i) === panelId);
            const isCollapsed = collapsedPanels.value[panelId];
            const w = Math.min(Math.max(meta.minW, item?.w ?? meta.defaultW), 12);
            const x = Math.max(0, Math.min(item?.x ?? meta.defaultX, 12 - w));
            return {
                i: panelId,
                x,
                y: item?.y ?? meta.defaultY,
                w,
                h: isCollapsed ? COLLAPSED_H : Math.max(meta.minH, item?.h ?? meta.defaultH),
                minW: meta.minW,
                minH: isCollapsed ? COLLAPSED_H : meta.minH,
            };
        });
    };

    watch(panelLayout, persistLayoutState, { deep: true });
    watch(panelVisibility, persistLayoutState, { deep: true });

    return {
        panelVisibility,
        collapsedPanels,
        visiblePanelLayout,
        resetLayout,
        setPanelVisibility,
        toggleCollapse,
        handleLayoutUpdate,
    };
}
