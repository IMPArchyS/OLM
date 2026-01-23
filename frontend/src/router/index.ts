import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useUserStore } from '@/stores/user';
import MainLayout from '@/layouts/MainLayout.vue';
import AuthLayout from '@/layouts/AuthLayout.vue';
import dashboard from '@/views/app/Dashboard.vue';
import queue from '@/views/app/Queue.vue';
import reservations from '@/views/app/Reservations.vue';
import reports from '@/views/app/Reports.vue';
import servers from '@/views/app/servers/Servers.vue';
import login from '@/views/auth/Login.vue';
import register from '@/views/auth/Register.vue';
import error404 from '@/views/errors/Error404.vue';
import error500 from '@/views/errors/Error500.vue';
import updateProfile from '@/views/app/users/UpdateProfile.vue';
import updatePassword from '@/views/app/users/UpdatePassword.vue';

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            redirect: '/auth/login',
        },
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
            meta: { requiresAuth: true },
            children: [
                {
                    path: '',
                    redirect: '/app/dashboard',
                },
                {
                    path: '/app/update-profile',
                    name: 'update-profile',
                    component: updateProfile,
                },
                {
                    path: '/app/update-password',
                    name: 'update-password',
                    component: updatePassword,
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
                    path: '/app/servers/create',
                    name: 'servers-create',
                    component: () => import('@/views/app/servers/CreateServer.vue'),
                },
                {
                    path: '/app/servers/:id/show',
                    name: 'servers-show',
                    component: () => import('@/views/app/servers/ShowServer.vue'),
                },
                {
                    path: '/app/servers/:id/edit',
                    name: 'servers-edit',
                    component: () => import('@/views/app/servers/EditServer.vue'),
                },
                {
                    path: '/app/schemas',
                    name: 'schemas-index',
                    component: () => import('@/views/app/schemas/Schemas.vue'),
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
                {
                    path: '/app/users',
                    name: 'users',
                    component: () => import('@/views/app/users/Users.vue'),
                },
                {
                    path: '/app/roles',
                    name: 'roles',
                    component: () => import('@/views/app/roles/Roles.vue'),
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
});

// Track if auth has been initialized
let authInitialized = false;

// Navigation guard to protect routes
router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore();

    // Initialize auth on first navigation (attempt session recovery from cookie)
    if (!authInitialized) {
        await authStore.initAuth();
        authInitialized = true;
    }

    // Check if route requires authentication
    const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);

    if (requiresAuth) {
        // Route requires authentication
        if (!authStore.isAuthenticated) {
            // Try to recover session one more time before redirecting
            const recovered = await authStore.initAuth();

            if (!recovered) {
                // Still not authenticated, redirect to login
                next({
                    name: 'login',
                    query: { redirect: to.fullPath }, // Save the intended destination
                });
                return;
            }
        }

        // Authenticated, allow access
        next();
    } else {
        // Route doesn't require auth
        if (authStore.isAuthenticated && (to.name === 'login' || to.name === 'register')) {
            // Already logged in, redirect to dashboard
            next({ name: 'dashboard' });
        } else {
            next();
        }
    }
});

export default router;
