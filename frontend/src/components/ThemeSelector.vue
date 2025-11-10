<script setup lang="ts">
import { useThemeStore } from '@/stores/theme'
import { useTheme } from 'vuetify'
import { computed, watch } from 'vue'

const themeStore = useThemeStore()
const vuetifyTheme = useTheme()

const isDark = computed(() => vuetifyTheme.global.name.value === 'dark')

watch(
    () => themeStore.theme,
    (newTheme) => {
        vuetifyTheme.change(newTheme)
    },
    { immediate: true },
)

const toggleTheme = () => {
    const newTheme = isDark.value ? 'light' : 'dark'
    vuetifyTheme.change(newTheme)
    themeStore.theme = newTheme
}
</script>

<template>
    <v-btn
        :icon="isDark ? 'mdi-weather-night' : 'mdi-weather-sunny'"
        @click="toggleTheme"
        variant="text"
    />
</template>
