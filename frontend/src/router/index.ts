import { createRouter, createWebHistory } from 'vue-router';
import { authStore } from '@/main';

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            redirect: '/auth/login',
        },
        {
            path: '/auth',
            component: () => import('@/layouts/MainLayout.vue'),
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
                    component: () => import('@/views/app/user/UpdateProfile.vue'),
                },
                {
                    path: '/app/update-password',
                    name: 'update-password',
                    component: () => import('@/views/app/user/UpdatePassword.vue'),
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
                    meta: { permission: 'olm.server.read' },
                },
                {
                    path: '/app/servers/create',
                    name: 'servers-create',
                    component: () => import('@/views/app/servers/CreateServer.vue'),
                    meta: { permission: 'olm.server.create' },
                },
                {
                    path: '/app/servers/:id/show',
                    name: 'servers-show',
                    component: () => import('@/views/app/servers/ShowServer.vue'),
                    meta: { permission: 'olm.server.read' },
                },
                {
                    path: '/app/servers/:id/edit',
                    name: 'servers-edit',
                    component: () => import('@/views/app/servers/EditServer.vue'),
                    meta: { permission: 'olm.server.update' },
                },
                {
                    path: '/app/experiments',
                    name: 'experiments',
                    component: () => import('@/views/app/experiments/Experiments.vue'),
                    meta: { permission: 'olm.experiment.read' },
                },
                {
                    path: '/app/experiments/create',
                    name: 'experiments-create',
                    component: () => import('@/views/app/experiments/CreateExperiment.vue'),
                    meta: { permission: 'olm.experiment.create' },
                },
                {
                    path: '/app/experiments/:id/show',
                    name: 'experiments-show',
                    component: () => import('@/views/app/experiments/ShowExperiment.vue'),
                    meta: { permission: 'olm.experiment.read' },
                },
                {
                    path: '/app/experiments/:id/edit',
                    name: 'experiments-edit',
                    component: () => import('@/views/app/experiments/EditExperiment.vue'),
                    meta: { permission: 'olm.experiment.update' },
                },
            ],
        },
        {
            path: '/:pathMatch(.*)*',
            name: 'notFound',
            component: () => import('@/views/errors/Error404.vue'),
        },
        { path: '/403', component: () => import('@/views/errors/Error403.vue') },
        {
            path: '/500',
            name: 'serverError',
            component: () => import('@/views/errors/Error500.vue'),
        },
    ],
});

router.onError((err, to) => {
    if (err?.message?.includes?.('Failed to fetch dynamically imported module')) {
        if (!localStorage.getItem('vuetify:dynamic-reload')) {
            console.log('Reloading page to fix dynamic import error');
            localStorage.setItem('vuetify:dynamic-reload', 'true');
            location.assign(to.fullPath);
        } else {
            console.error('Dynamic import error, reloading page did not fix it', err);
        }
    } else {
        console.error(err);
    }
});

router.beforeEach(async (to, from, next) => {
    const backendPaths = ['/api', '/docs', '/redoc', '/openapi.json', '/ws', '/ovl-auth'];
    const authRoutes = ['/auth/login', '/auth/register'];
    const requiredPermission = to.meta.permission as string;

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

    if (requiredPermission && !authStore.can(requiredPermission)) {
        return next({ path: '/403' });
    }

    if (to.meta.requiresAuth) {
        if (!authStore.accessToken) {
            await authStore.initAuth();
        }

        if (!authStore.accessToken) {
            return next({ path: '/auth/login' });
        }

        return next();
    }
    next();
});

router.isReady().then(() => {
    localStorage.removeItem('vuetify:dynamic-reload');
});

export default router;
