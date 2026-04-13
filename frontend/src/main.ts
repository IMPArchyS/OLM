import App from './App.vue';

import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { useAuthStore } from './stores/auth';

import vuetify from './plugins/vuetify';
import i18n from '@/lib/i18n';
import router from './router';

import '../index.css';

const pinia = createPinia();
const app = createApp(App);

app.use(pinia).use(i18n).use(vuetify);

const authStore = useAuthStore();

authStore.initAuth().finally(() => {
    app.use(router);
    router.isReady().then(async () => {
        app.mount('#app');
    });
});

export { authStore };
