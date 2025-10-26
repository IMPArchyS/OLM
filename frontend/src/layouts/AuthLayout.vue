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
    <div class="flex h-screen overflow-hidden">
        <div class="flex-1 flex flex-col overflow-hidden bg-base-100">
            <NavBar />
            <main class="flex-1 px-7! mb-5! overflow-y-auto">
                <router-view />
            </main>
        </div>
    </div>
</template>
