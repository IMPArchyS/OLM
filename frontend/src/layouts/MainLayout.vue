<script setup lang="ts">
import { useMainLayout } from '@/composables/useMainLayout';
import { useToast } from '@/composables/useToast';
import Sidebar from './Sidebar.vue';
import NavBar from './NavBar.vue';
import { provide } from 'vue';

const { sidebarCollapsed, sidebarVisible, windowWidth, toggleSidebar, toggleSidebarVisibility } = useMainLayout();

const { snackbar, snackbarText, snackbarColor, snackbarTimeout } = useToast();

// Provide the layout state and functions to child components
provide('mainLayout', {
    sidebarCollapsed,
    sidebarVisible,
    windowWidth,
    toggleSidebar,
    toggleSidebarVisibility,
});
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

        <!-- Global Toast/Snackbar -->
        <v-snackbar v-model="snackbar" :color="snackbarColor" :timeout="snackbarTimeout" location="bottom center">
            {{ snackbarText }}
            <template v-slot:actions>
                <v-btn variant="text" @click="snackbar = false"> Close </v-btn>
            </template>
        </v-snackbar>
    </v-app>
</template>
