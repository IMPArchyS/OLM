<script setup lang="ts">
import LanguageSelector from '@/components/LanguageSelector.vue'
import ThemeSelector from '@/components/ThemeSelector.vue'
import UserSelector from '@/components/UserSelector.vue'
import { useMainLayout } from '@/composables/useMainLayout'
import NavBar from './NavBar.vue'
import { provide } from 'vue'

const { windowWidth, navItems, settingsItems, isActiveRoute, navigate } = useMainLayout()

// Provide the layout state and functions to child components
provide('mainLayout', {
    windowWidth,
    navItems,
    settingsItems,
    isActiveRoute,
    navigate,
})
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
