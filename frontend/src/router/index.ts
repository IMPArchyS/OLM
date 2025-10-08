import { createRouter, createWebHistory } from 'vue-router'
import dashboard from '@/views/Dashboard.vue'
import queue from '@/views/Queue.vue'
import reservations from '@/views/Reservations.vue'
import reports from '@/views/Reports.vue'
import servers from '@/views/Servers.vue'
import schemas from '@/views/Schemas.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/dashboard',
            name: 'dashboard',
            component: dashboard,
        },
        {
            path: '/queue',
            name: 'queue',
            component: queue,
        },
        {
            path: '/reservations',
            name: 'reservations',
            component: reservations,
        },
        {
            path: '/reports',
            name: 'reports',
            component: reports,
        },
        {
            path: '/servers',
            name: 'servers',
            component: servers,
        },
        {
            path: '/schemas',
            name: 'schemas',
            component: schemas,
        },
    ],
})

export default router
