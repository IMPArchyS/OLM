import { createI18n } from 'vue-i18n'
import en from './locales/en'
import sk from './locales/sk'

// Get initial locale from localStorage or default to 'en'
const savedLocale = localStorage.getItem('language') || 'en'

const i18n = createI18n({
    legacy: false, // Use Composition API mode
    locale: savedLocale,
    fallbackLocale: 'en',
    messages: {
        en,
        sk,
    },
})

export default i18n
