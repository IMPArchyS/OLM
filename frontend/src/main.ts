import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { vClickOutside } from './directives/clickOutside';
import { useAuthStore } from './stores/auth';
import i18n from './i18n';
import vuetify from './plugins/vuetify';

import App from './App.vue';
import router from './router';
import '../index.css';

const app = createApp(App);
app.directive('click-outside', vClickOutside);
app.use(createPinia());
app.use(i18n);
app.use(vuetify);

app.use(router);
router.isReady().then(async () => {
    app.mount('#app');
});
