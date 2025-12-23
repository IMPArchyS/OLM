import 'vuetify/styles';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';
import '@mdi/font/css/materialdesignicons.css';

const vuetify = createVuetify({
    components,
    directives,
    theme: {
        defaultTheme: 'light',
        themes: {
            light: {
                dark: false,
                colors: {
                    primary: '#3b82f6',
                    secondary: '#6b7280',
                    error: '#ef4444',
                    success: '#10b981',
                    background: '#ffffff',
                    surface: '#ffffff',
                    'surface-variant': '#f5f5f5',
                    'on-surface': '#000000',
                    'on-surface-variant': '#424242',
                },
            },
            dark: {
                dark: true,
                colors: {
                    primary: '#3b82f6',
                    secondary: '#6b7280',
                    error: '#ef4444',
                    success: '#10b981',
                    background: '#121212',
                    surface: '#1e1e1e',
                    'surface-variant': '#2c2c2c',
                    'on-surface': '#ffffff',
                    'on-surface-variant': '#e0e0e0',
                },
            },
        },
    },
});

export default vuetify;
