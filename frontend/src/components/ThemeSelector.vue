<script setup lang="ts">
import { useThemeStore } from '@/stores/theme'
import { computed } from 'vue'

const themeStore = useThemeStore()

const isDark = computed(() => themeStore.theme === 'dark')
</script>

<template>
    <v-btn
        :icon="isDark ? 'mdi-weather-night' : 'mdi-weather-sunny'"
        @click="themeStore.toggleTheme"
        variant="text"
    />
</template>
