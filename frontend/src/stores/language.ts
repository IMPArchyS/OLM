// stores/language.ts
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

export interface Language {
    code: string
    name: string
    flag: string
}

export const useLanguageStore = defineStore('language', () => {
    // Available languages - easy to add more!
    const languages = ref<Language[]>([
        { code: 'en', name: 'English', flag: '🇬🇧' },
        { code: 'sk', name: 'Slovenčina', flag: '🇸🇰' },
    ])

    const currentLanguage = ref<Language>(
        languages.value[0] ?? { code: 'en', name: 'English', flag: '🇬🇧' },
    )

    // Initialize language from localStorage or default to English
    const initLanguage = () => {
        const savedLangCode = localStorage.getItem('language')
        if (savedLangCode) {
            const found = languages.value.find((lang) => lang.code === savedLangCode)
            if (found) {
                currentLanguage.value = found
            }
        }
        applyLanguage(currentLanguage.value.code)
    }

    // Apply language (integrate with i18n here)
    const applyLanguage = (langCode: string) => {
        document.documentElement.setAttribute('lang', langCode)
        // Note: i18n locale change is handled in the component using useI18n
    }

    // Set language
    const setLanguage = (langCode: string) => {
        const found = languages.value.find((lang) => lang.code === langCode)
        if (found) {
            currentLanguage.value = found
        }
    }

    // Watch for language changes and persist
    watch(currentLanguage, (newLang) => {
        localStorage.setItem('language', newLang.code)
        applyLanguage(newLang.code)
    })

    return {
        languages,
        currentLanguage,
        initLanguage,
        setLanguage,
    }
})
