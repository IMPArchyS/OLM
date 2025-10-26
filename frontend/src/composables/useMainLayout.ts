import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

export interface NavItem {
    id: string
    icon: string
    label: string
    route: string
}

export function useMainLayout() {
    const router = useRouter()
    const route = useRoute()

    const sidebarCollapsed = ref(false)
    const sidebarVisible = ref(window.innerWidth > 720)
    const windowWidth = ref(window.innerWidth)

    const navItems: NavItem[] = [
        { id: 'dashboard', icon: '📊', label: 'Dashboard', route: '/app/dashboard' },
        { id: 'queue', icon: '⏱️', label: 'Queue experiments', route: '/app/queue' },
        { id: 'reservations', icon: '📅', label: 'Reservations', route: '/app/reservations' },
        { id: 'reports', icon: '📄', label: 'Reports', route: '/app/reports' },
    ]

    const settingsItems: NavItem[] = [
        { id: 'servers', icon: '🔬', label: 'Servers', route: '/app/servers' },
        { id: 'schemas', icon: '📋', label: 'Schemas', route: '/app/schemas' },
    ]

    const isActiveRoute = (routePath: string) => {
        return route.path === routePath
    }

    const navigate = (routePath: string) => {
        router.push(routePath)
    }

    const updateWindowWidth = () => {
        windowWidth.value = window.innerWidth
        // Sidebar hidden by default at < 720px
        if (windowWidth.value < 720) {
            sidebarVisible.value = false
            sidebarCollapsed.value = false
        }
    }

    // Arrow toggles collapse only at >= 920px
    const toggleSidebar = () => {
        if (windowWidth.value >= 920) {
            sidebarCollapsed.value = !sidebarCollapsed.value
        }
    }

    // Hamburger always toggles sidebar visibility
    const toggleSidebarVisibility = () => {
        sidebarVisible.value = !sidebarVisible.value
        // At < 720px, always expanded when visible
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
        navItems,
        settingsItems,
        isActiveRoute,
        navigate,
        toggleSidebar,
        toggleSidebarVisibility,
    }
}
