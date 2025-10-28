<script setup lang="ts">
import LanguageSelector from '@/components/LanguageSelector.vue'
import ThemeSelector from '@/components/ThemeSelector.vue'
import UserSelector from '@/components/UserSelector.vue'
import { useMainLayout } from '@/composables/useMainLayout'
import Sidebar from './Sidebar.vue'
import NavBar from './NavBar.vue'
import { provide } from 'vue'

const {
    sidebarCollapsed,
    sidebarVisible,
    windowWidth,
    navItems,
    settingsItems,
    isActiveRoute,
    navigate,
    toggleSidebar,
    toggleSidebarVisibility,
} = useMainLayout()

// Provide the layout state and functions to child components
provide('mainLayout', {
    sidebarCollapsed,
    sidebarVisible,
    windowWidth,
    navItems,
    settingsItems,
    isActiveRoute,
    navigate,
    toggleSidebar,
    toggleSidebarVisibility,
})
</script>

<template>
    <v-app>
        <Sidebar />
        <NavBar />
        <v-main>
            <div class="px-7 mb-5">
                <router-view />
            </div>
        </v-main>
    </v-app>
</template>
