import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { vClickOutside } from './directives/clickOutside';
import i18n from '@/lib/i18n';
import vuetify from './plugins/vuetify';

import App from './App.vue';
import router from './router';
import '../index.css';

const pinia = createPinia();
const app = createApp(App);

app.directive('click-outside', vClickOutside);
app.use(pinia).use(i18n).use(vuetify);

app.use(router);
router.isReady().then(async () => {
    app.mount('#app');
});
