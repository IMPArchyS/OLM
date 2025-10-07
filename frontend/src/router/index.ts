import { createRouter, createWebHistory } from 'vue-router'
import dashboard from '@/views/Dashboard.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/dashboard',
            name: 'dashboard',
            component: dashboard,
        },
    ],
})

export default router
