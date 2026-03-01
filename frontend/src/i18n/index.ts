import { createI18n } from 'vue-i18n';
import en from './locales/en';
import sk from './locales/sk';

const savedLocale = localStorage.getItem('language') || 'en';

const i18n = createI18n({
    legacy: false,
    locale: savedLocale,
    fallbackLocale: 'en',
    messages: {
        en,
        sk,
    },
});

export default i18n;
