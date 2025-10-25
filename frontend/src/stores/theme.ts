// stores/theme.ts
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
    const theme = ref<'light' | 'dark'>('light')

    // Initialize theme from localStorage or default to light
    const initTheme = () => {
        const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
        if (savedTheme) {
            theme.value = savedTheme
        }
        applyTheme(theme.value)
    }

    // Apply theme to document
    const applyTheme = (newTheme: 'light' | 'dark') => {
        document.documentElement.setAttribute('data-theme', newTheme)
    }

    // Toggle between light and dark
    const toggleTheme = () => {
        theme.value = theme.value === 'light' ? 'dark' : 'light'
    }

    // Watch for theme changes and persist
    watch(theme, (newTheme) => {
        localStorage.setItem('theme', newTheme)
        applyTheme(newTheme)
    })

    return {
        theme,
        initTheme,
        toggleTheme,
    }
})
