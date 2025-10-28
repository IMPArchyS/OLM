import { ref, onMounted, onUnmounted } from 'vue'

export function useMainLayout() {
    const sidebarCollapsed = ref(false)
    const sidebarVisible = ref(window.innerWidth > 720)
    const windowWidth = ref(window.innerWidth)

    const updateWindowWidth = () => {
        windowWidth.value = window.innerWidth
        // Hide sidebar on mobile by default
        if (windowWidth.value < 720) {
            sidebarVisible.value = false
            sidebarCollapsed.value = false
        }
    }

    // Toggle collapse (only works at >= 920px)
    const toggleSidebar = () => {
        if (windowWidth.value >= 920) {
            sidebarCollapsed.value = !sidebarCollapsed.value
        }
    }

    // Toggle visibility (hamburger menu)
    const toggleSidebarVisibility = () => {
        sidebarVisible.value = !sidebarVisible.value
        // Always expanded when visible on mobile
        if (windowWidth.value < 720 && sidebarVisible.value) {
            sidebarCollapsed.value = false
        }
    }

    onMounted(() => {
        window.addEventListener('resize', updateWindowWidth)
    })

    onUnmounted(() => {
        window.removeEventListener('resize', updateWindowWidth)
    })

    return {
        sidebarCollapsed,
        sidebarVisible,
        windowWidth,
        toggleSidebar,
        toggleSidebarVisibility,
    }
}
