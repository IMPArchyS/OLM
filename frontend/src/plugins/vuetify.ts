import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

const vuetify = createVuetify({
    components,
    directives,
    theme: {
        defaultTheme: 'light',
        themes: {
            light: {
                colors: {
                    primary: '#3b82f6',
                    secondary: '#6b7280',
                    error: '#ef4444',
                    success: '#10b981',
                },
            },
            dark: {
                colors: {
                    primary: '#3b82f6',
                    secondary: '#6b7280',
                    error: '#ef4444',
                    success: '#10b981',
                },
            },
        },
    },
})

export default vuetify
