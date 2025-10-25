<script setup lang="ts">
import { useThemeStore } from '@/stores/theme'
import { computed } from 'vue'

const themeStore = useThemeStore()

const isDark = computed(() => themeStore.theme === 'dark')
</script>

<template>
    <label class="swap swap-rotate">
        <!-- Hidden checkbox -->
        <input
            type="checkbox"
            :checked="isDark"
            @change="themeStore.toggleTheme"
            class="theme-controller"
        />

        <!-- Sun icon (light mode) -->
        <span class="swap-off text-2xl">☀️</span>

        <!-- Moon icon (dark mode) -->
        <span class="swap-on text-2xl">🌙</span>
    </label>
</template>

<style scoped>
.swap {
    cursor: pointer;
    user-select: none;
}

.theme-controller {
    position: absolute;
    opacity: 0;
    pointer-events: none;
}

/* Simple fade transition */
.swap-off,
.swap-on {
    transition:
        opacity 0.3s ease,
        transform 0.3s ease;
}

.swap input:not(:checked) ~ .swap-on {
    opacity: 0;
    transform: rotate(180deg);
}

.swap input:checked ~ .swap-off {
    opacity: 0;
    transform: rotate(-180deg);
}
</style>
