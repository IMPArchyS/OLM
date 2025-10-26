import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'
import dashboard from '@/views/Dashboard.vue'
import queue from '@/views/Queue.vue'
import reservations from '@/views/Reservations.vue'
import reports from '@/views/Reports.vue'
import servers from '@/views/Servers.vue'
import schemas from '@/views/Schemas.vue'
import login from '@/views/auth/Login.vue'
import register from '@/views/auth/Register.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        // Auth routes at root level - uses AuthLayout
        {
            path: '/auth',
            component: AuthLayout,
            children: [
                {
                    path: '',
                    redirect: '/auth/login',
                },
                {
                    path: '/auth/login',
                    name: 'login',
                    component: login,
                },
                {
                    path: '/auth/register',
                    name: 'register',
                    component: register,
                },
            ],
        },
        // Main app routes under /app - uses MainLayout
        {
            path: '/app',
            component: MainLayout,
            // meta: { requiresAuth: true }, // Uncomment when ready to enforce auth
            children: [
                {
                    path: '',
                    redirect: '/app/dashboard',
                },
                {
                    path: '/app/dashboard',
                    name: 'dashboard',
                    component: dashboard,
                },
                {
                    path: '/app/queue',
                    name: 'queue',
                    component: queue,
                },
                {
                    path: '/app/reservations',
                    name: 'reservations',
                    component: reservations,
                },
                {
                    path: '/app/reports',
                    name: 'reports',
                    component: reports,
                },
                {
                    path: '/app/servers',
                    name: 'servers',
                    component: servers,
                },
                {
                    path: '/app/schemas',
                    name: 'schemas',
                    component: schemas,
                },
            ],
        },
    ],
})

// Navigation guard to check authentication
// router.beforeEach((to, from, next) => {
//     const isAuthenticated = checkAuth() // Implement your auth check logic

//     if (to.meta.requiresAuth && !isAuthenticated) {
//         next({ name: 'login' })
//     } else if (to.path.startsWith('/auth') && isAuthenticated) {
//         next({ name: 'dashboard' })
//     } else {
//         next()
//     }
// })

// function checkAuth(): boolean {
//     // TODO: Implement your authentication check
//     // Example: Check if user token exists in localStorage or store
//     // return !!localStorage.getItem('authToken')
//     return true // Temporary - always authenticated
// }

export default router
