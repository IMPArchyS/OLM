import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'
import dashboard from '@/views/app/Dashboard.vue'
import queue from '@/views/app/Queue.vue'
import reservations from '@/views/app/Reservations.vue'
import reports from '@/views/app/Reports.vue'
import servers from '@/views/app/Servers.vue'
import login from '@/views/auth/Login.vue'
import register from '@/views/auth/Register.vue'
import error404 from '@/views/errors/Error404.vue'
import error500 from '@/views/errors/Error500.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
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
                    name: 'schemas-index',
                    component: () => import('@/views/app/schemas/IndexSchema.vue'),
                    meta: {
                        requiresAuth: true,
                        permission: 'schema.index',
                    },
                },
                {
                    path: '/app/schemas/create',
                    name: 'schemas-create',
                    component: () => import('@/views/app/schemas/CreateSchema.vue'),
                    meta: {
                        requiresAuth: true,
                        permission: 'schema.create',
                    },
                },
                {
                    path: '/app/schemas/:id/edit',
                    name: 'schemas-edit',
                    component: () => import('@/views/app/schemas/EditSchema.vue'),
                    meta: {
                        requiresAuth: true,
                        permission: 'schema.update',
                    },
                },
            ],
        },
        {
            path: '/:pathMatch(.*)*',
            name: 'notFound',
            component: error404,
        },
        {
            path: '/500',
            name: 'serverError',
            component: error500,
        },
    ],
})

export default router
