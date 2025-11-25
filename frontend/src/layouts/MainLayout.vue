<script setup lang="ts">
import { useMainLayout } from '@/composables/useMainLayout'
import Sidebar from './Sidebar.vue'
import NavBar from './NavBar.vue'
import { provide } from 'vue'

const { sidebarCollapsed, sidebarVisible, windowWidth, toggleSidebar, toggleSidebarVisibility } =
    useMainLayout()

// Provide the layout state and functions to child components
provide('mainLayout', {
    sidebarCollapsed,
    sidebarVisible,
    windowWidth,
    toggleSidebar,
    toggleSidebarVisibility,
})
</script>

<template>
    <v-app>
        <Sidebar />
        <NavBar />
        <v-main style="height: 100vh; overflow-y: auto; overflow-x: hidden">
            <div class="px-7 mb-5">
                <router-view />
            </div>
        </v-main>
    </v-app>
</template>
