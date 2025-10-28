<script setup lang="ts">
import { useThemeStore } from '@/stores/theme'
import { useTheme } from 'vuetify'
import { computed, watch } from 'vue'

const themeStore = useThemeStore()
const vuetifyTheme = useTheme()

// Computed property to check if dark mode is active
const isDark = computed(() => vuetifyTheme.global.name.value === 'dark')

// Watch for changes in the store and apply to Vuetify
watch(
    () => themeStore.theme,
    (newTheme) => {
        vuetifyTheme.global.name.value = newTheme
    },
    { immediate: true },
)

// Toggle theme function
const toggleTheme = () => {
    const newTheme = isDark.value ? 'light' : 'dark'
    vuetifyTheme.global.name.value = newTheme
    themeStore.theme = newTheme // Sync with store for persistence
}
</script>

<template>
    <v-btn
        :icon="isDark ? 'mdi-weather-night' : 'mdi-weather-sunny'"
        @click="toggleTheme"
        variant="text"
    />
</template>
