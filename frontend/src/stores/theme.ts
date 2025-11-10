import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
    const theme = ref<'light' | 'dark'>('light')

    const initTheme = () => {
        const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
        if (savedTheme) {
            theme.value = savedTheme
        }
        applyTheme(theme.value)
    }

    const applyTheme = (newTheme: 'light' | 'dark') => {}

    const toggleTheme = () => {
        theme.value = theme.value === 'light' ? 'dark' : 'light'
    }

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
