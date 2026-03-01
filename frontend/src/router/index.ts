import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            redirect: '/auth/login',
        },
        {
            path: '/auth',
            component: () => import('@/layouts/AuthLayout.vue'),
            children: [
                {
                    path: '',
                    redirect: '/auth/login',
                },
                {
                    path: '/auth/login',
                    name: 'login',
                    component: () => import('@/views/auth/Login.vue'),
                },
                {
                    path: '/auth/register',
                    name: 'register',
                    component: () => import('@/views/auth/Register.vue'),
                },
            ],
        },
        {
            path: '/auth/callback',
            name: 'callback',
            component: () => import('@/views/auth/Callback.vue'),
        },
        {
            path: '/app',
            component: () => import('@/layouts/MainLayout.vue'),
            meta: { requiresAuth: true },
            children: [
                {
                    path: '',
                    redirect: '/app/dashboard',
                },
                {
                    path: '/app/update-profile',
                    name: 'update-profile',
                    component: () => import('@/views/auth/UpdateProfile.vue'),
                },
                {
                    path: '/app/update-password',
                    name: 'update-password',
                    component: () => import('@/views/auth/UpdatePassword.vue'),
                },
                {
                    path: '/app/dashboard',
                    name: 'dashboard',
                    component: () => import('@/views/app/Dashboard.vue'),
                },
                {
                    path: '/app/queue',
                    name: 'queue',
                    component: () => import('@/views/app/Queue.vue'),
                },
                {
                    path: '/app/reservations',
                    name: 'reservations',
                    component: () => import('@/views/app/Reservations.vue'),
                },
                {
                    path: '/app/reports',
                    name: 'reports',
                    component: () => import('@/views/app/Reports.vue'),
                },
                {
                    path: '/app/servers',
                    name: 'servers',
                    component: () => import('@/views/app/servers/Servers.vue'),
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
            ],
        },
        {
            path: '/:pathMatch(.*)*',
            name: 'notFound',
            component: () => import('@/views/errors/Error404.vue'),
        },
        {
            path: '/500',
            name: 'serverError',
            component: () => import('@/views/errors/Error500.vue'),
        },
    ],
});

router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore();

    const backendPaths = ['/api', '/docs', '/redoc', '/openapi.json', '/ws', '/ovl-auth'];
    const authRoutes = ['/auth/login', '/auth/register'];

    if (backendPaths.some((path) => to.path.startsWith(path))) {
        window.location.href = to.fullPath;
        return;
    }

    if (authRoutes.includes(to.path)) {
        if (!authStore.accessToken) {
            await authStore.initAuth();
        }

        if (authStore.accessToken) {
            return next({ path: '/app/dashboard' });
        }
    }

    if (to.meta.requiresAuth || to.meta.requiresOlmAdmin) {
        if (!authStore.accessToken) {
            await authStore.initAuth();
        }

        if (!authStore.accessToken) {
            return next({ path: '/auth/login' });
        }

        if (to.meta.requiresOlmAdmin) {
            await authStore.fetchRoleName();
            const isOlmAdmin = authStore.roleName;
            if (isOlmAdmin !== 'olm_admin') {
                return next({ path: '/' });
            }
        }
        return next();
    }
    next();
});

export default router;
