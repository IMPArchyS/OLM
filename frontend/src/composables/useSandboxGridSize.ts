import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useResizeObserver } from '@vueuse/core';

const MOBILE_BREAKPOINT = 960;

export function useSandboxGridSize() {
    const gridContainerRef = ref<HTMLElement | null>(null);
    const isMobile = ref(false);
    const gridRowHeight = ref(10);
    const gridHeight = ref(600);

    const updateGridHeight = () => {
        const el = gridContainerRef.value;
        if (!el) return;
        const top = el.getBoundingClientRect().top;
        gridHeight.value = Math.max(400, window.innerHeight - top - 32);
    };

    useResizeObserver(gridContainerRef, (entries) => {
        const width = entries[0]?.contentRect.width ?? 0;
        isMobile.value = width > 0 && width <= MOBILE_BREAKPOINT;
        gridRowHeight.value = width < 700 ? 8 : width < 960 ? 9 : 10;
        updateGridHeight();
    });

    onMounted(() => {
        updateGridHeight();
        window.addEventListener('resize', updateGridHeight);
    });

    onBeforeUnmount(() => {
        window.removeEventListener('resize', updateGridHeight);
    });

    return { gridContainerRef, isMobile, gridRowHeight, gridHeight };
}
