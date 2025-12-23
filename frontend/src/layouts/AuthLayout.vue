<script setup lang="ts">
import { useMainLayout } from '@/composables/useMainLayout';
import NavBar from './NavBar.vue';
import { provide } from 'vue';

const { windowWidth } = useMainLayout();

// Provide the layout state and functions to child components
provide('mainLayout', {
    windowWidth,
});
</script>

<template>
    <v-app>
        <NavBar />
        <v-main>
            <div class="px-7 mb-5">
                <router-view />
            </div>
        </v-main>
    </v-app>
</template>
