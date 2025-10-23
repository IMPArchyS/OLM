<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import LanguageSelector from '@/components/LanguageSelector.vue'

const router = useRouter()
const route = useRoute()

const sidebarCollapsed = ref(false)
const sidebarVisible = ref(window.innerWidth > 720)
const windowWidth = ref(window.innerWidth)

interface NavItem {
    id: string
    icon: string
    label: string
    route: string
}

const navItems: NavItem[] = [
    { id: 'dashboard', icon: '📊', label: 'Dashboard', route: '/dashboard' },
    { id: 'queue', icon: '⏱️', label: 'Queue experiments', route: '/queue' },
    { id: 'reservations', icon: '📅', label: 'Reservations', route: '/reservations' },
    { id: 'reports', icon: '📄', label: 'Reports', route: '/reports' },
]

const settingsItems: NavItem[] = [
    { id: 'servers', icon: '🔬', label: 'Servers', route: '/servers' },
    { id: 'schemas', icon: '📋', label: 'Schemas', route: '/schemas' },
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

onMounted(() => {
    window.addEventListener('resize', updateWindowWidth)
})
onUnmounted(() => {
    window.removeEventListener('resize', updateWindowWidth)
})

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
</script>

<template>
    <div class="layout">
        <!-- Sidebar -->
        <aside :class="['sidebar', { collapsed: sidebarCollapsed, hidden: !sidebarVisible }]">
            <!-- Header -->
            <div class="sidebar-header">
                <div v-if="!sidebarCollapsed" class="logo">
                    <div class="logo-title">ONLINE LABORATORY</div>
                    <div class="logo-subtitle">MANAGER</div>
                </div>
                <div v-if="sidebarCollapsed" class="logo">
                    <div class="logo-title">OLM</div>
                </div>
            </div>

            <!-- Navigation -->
            <nav class="sidebar-nav">
                <!-- Main Navigation -->
                <div class="nav-section">
                    <div v-if="!sidebarCollapsed" class="nav-section-title">LAB</div>
                    <button
                        v-for="item in navItems"
                        :key="item.id"
                        @click="navigate(item.route)"
                        :class="['nav-item', { active: isActiveRoute(item.route) }]"
                        :title="sidebarCollapsed ? item.label : ''"
                    >
                        <span class="nav-icon">{{ item.icon }}</span>
                        <span v-if="!sidebarCollapsed" class="nav-label">{{ item.label }}</span>
                    </button>
                </div>

                <!-- Settings Navigation -->
                <div class="nav-section">
                    <div v-if="!sidebarCollapsed" class="nav-section-title">SETTINGS</div>
                    <button
                        v-for="item in settingsItems"
                        :key="item.id"
                        @click="navigate(item.route)"
                        :class="['nav-item', { active: isActiveRoute(item.route) }]"
                        :title="sidebarCollapsed ? item.label : ''"
                    >
                        <span class="nav-icon">{{ item.icon }}</span>
                        <span v-if="!sidebarCollapsed" class="nav-label">{{ item.label }}</span>
                    </button>
                </div>
            </nav>
            <div class="sidebar-footer" v-if="windowWidth >= 920">
                <button @click="toggleSidebar" class="toggle-btn">
                    {{ sidebarCollapsed ? '>' : '<' }}
                </button>
            </div>
        </aside>
        <div
            v-if="sidebarVisible && windowWidth < 720"
            class="sidebar-overlay"
            @click="sidebarVisible = false"
        ></div>
        <!-- Main Content Area -->
        <div class="main-container">
            <header class="topbar">
                <div class="topbar-left">
                    <button @click="toggleSidebarVisibility" class="hamburger-btn">
                        <span class="hamburger-icon">☰</span>
                    </button>
                </div>
                <div class="topbar-actions">
                    <LanguageSelector />
                    <div class="user-menu">
                        <div class="user-avatar">U</div>
                        <span class="user-name">username</span>
                    </div>
                </div>
            </header>

            <main class="content">
                <router-view />
            </main>
        </div>
    </div>
</template>

<style scoped>
.layout {
    display: flex;
    height: 100vh;
    overflow: hidden;
}

/* Sidebar Styles */
.sidebar {
    width: 256px;
    background-color: #1e293b;
    color: white;
    display: flex;
    flex-direction: column;
    transition:
        width 0.3s ease,
        transform 0.3s ease;
    flex-shrink: 0;
    position: relative;
    z-index: 100;
}

.sidebar.collapsed {
    width: 64px;
}

.sidebar-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(30, 41, 59, 0.4); /* dark semi-transparent */
    z-index: 99; /* just below sidebar */
}

.sidebar.hidden {
    transform: translateX(-100%);
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: 100;
}

.sidebar-header {
    padding: 1rem;
    border-bottom: 1px solid #334155;
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 73px;
}

.sidebar-footer {
    padding: 1rem;
    border-top: 1px solid #334155;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    min-height: 73px;
}

.logo {
    font-size: 0.875rem;
    font-weight: 600;
    line-height: 1.3;
}

.logo-title {
    color: white;
}

.logo-subtitle {
    color: #94a3b8;
}

.toggle-btn {
    padding: 1rem;
    background: transparent;
    border: none;
    color: white;
    cursor: pointer;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.toggle-btn:hover {
    background-color: #334155;
}

.sidebar-nav {
    flex: 1;
    padding: 1rem 0;
    overflow-y: auto;
}

.nav-section {
    margin-bottom: 1.5rem;
}

.nav-section-title {
    padding: 0 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.nav-item {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: transparent;
    border: none;
    color: white;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
    font-size: 0.875rem;
    border-left: 4px solid transparent;
}

.nav-item:hover {
    background-color: #334155;
}

.nav-item.active {
    background-color: #334155;
    border-left-color: #3b82f6;
}

.nav-icon {
    font-size: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 20px;
}

.nav-label {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Main Container */
.main-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background-color: #f9fafb;
}

/* Top Bar */
.topbar {
    background-color: white;
    border-bottom: 1px solid #e5e7eb;
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.topbar-left {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.hamburger-btn {
    display: block;
    padding: 0.5rem;
    background: transparent;
    border: none;
    cursor: pointer;
    border-radius: 4px;
    transition: background-color 0.2s;
    font-size: 1.5rem;
    color: #374151;
}

.hamburger-btn:hover {
    background-color: #f3f4f6;
}

.hamburger-icon {
    display: flex;
    align-items: center;
    justify-content: center;
}

.page-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
    text-transform: capitalize;
}

.topbar-actions {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.icon-btn {
    padding: 0.5rem;
    background: transparent;
    border: none;
    border-radius: 9999px;
    cursor: pointer;
    transition: background-color 0.2s;
    font-size: 1.25rem;
}

.icon-btn:hover {
    background-color: #f3f4f6;
}

.user-menu {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
}

.user-avatar {
    width: 2rem;
    height: 2rem;
    background-color: #3b82f6;
    border-radius: 9999px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 0.875rem;
    font-weight: 600;
}

.user-name {
    font-size: 0.875rem;
    color: #374151;
}

/* Content Area */
.content {
    flex: 1;
    padding: 1.5rem;
    overflow-y: auto;
}
</style>
