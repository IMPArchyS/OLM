import { createI18n } from 'vue-i18n';
import en from '@/lib/locales/en';
import sk from '@/lib/locales/sk';

const messages = {
    en: en,
    sk: sk,
};

const i18n = createI18n({
    locale: localStorage.getItem('locale') ?? 'sk',
    fallbackLocale: 'en',
    messages,
});

export default i18n;
