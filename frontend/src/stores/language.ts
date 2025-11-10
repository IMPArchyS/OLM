import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

export interface Language {
    code: string
    name: string
    flag: string
}

const DEFAULT_LANGUAGE: Language = { code: 'en', name: 'English', flag: '🇬🇧' }

const AVAILABLE_LANGUAGES: Language[] = [
    DEFAULT_LANGUAGE,
    { code: 'sk', name: 'Slovenčina', flag: '🇸🇰' },
]

export const useLanguageStore = defineStore('language', () => {
    const { locale } = useI18n()

    const languages = ref<Language[]>(AVAILABLE_LANGUAGES)
    const currentLanguage = ref<Language>(DEFAULT_LANGUAGE)

    let isInitialized = false

    const applyLanguage = (langCode: string) => {
        locale.value = langCode
        document.documentElement.setAttribute('lang', langCode)
    }

    const setLanguage = (langCode: string) => {
        const found = languages.value.find((lang) => lang.code === langCode)
        if (found) {
            currentLanguage.value = found
        }
    }

    const initLanguage = () => {
        if (isInitialized) return

        const savedLangCode = localStorage.getItem('language')
        if (savedLangCode) {
            const found = languages.value.find((lang) => lang.code === savedLangCode)
            if (found) {
                currentLanguage.value = found
            }
        }

        applyLanguage(currentLanguage.value.code)
        isInitialized = true
    }

    watch(currentLanguage, (newLang) => {
        if (!isInitialized) return

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
