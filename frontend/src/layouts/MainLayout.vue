<script setup lang="ts">
import LanguageSelector from '@/components/layout/LanguageSelector.vue';
import UserSelector from '@/components/layout/UserSelector.vue';
import { useAuthStore } from '@/stores/auth';
import type { Role } from '@/types/authTypes';
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useDisplay, useTheme } from 'vuetify';

const theme = useTheme();
const router = useRouter();
const authStore = useAuthStore();
const display = useDisplay();

const isCollapsed = ref(false);
const isDrawerOpen = ref(false);

const handleThemeChange = () => {
    localStorage.setItem('theme', theme.global.current.value.dark ? 'light' : 'dark');
    theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark';
};

const handleMainClick = () => {
    if (display.smAndDown.value) {
        isCollapsed.value = false;
        isDrawerOpen.value = !isDrawerOpen.value;
    }
};

const handleCollapse = () => {
    isCollapsed.value = !isCollapsed.value;
    localStorage.setItem('isCollapsed', String(isCollapsed.value));
};

type NavItem = {
    i18nLabel: string;
    path: string;
    icon: string;
    roles?: Role[];
};

type NavSection = {
    key: string;
    i18nLabel: string;
    roles?: Role[];
    items: NavItem[];
};

const navSections: NavSection[] = [
    {
        key: 'common',
        i18nLabel: 'nav.lab',
        items: [
            { i18nLabel: 'nav.dashboard', path: '/app/dashboard', icon: 'mdi-view-dashboard' },
            { i18nLabel: 'nav.queue_experiments', path: '/app/queue', icon: 'mdi-clock-outline' },
            { i18nLabel: 'nav.reservations', path: '/app/reservations', icon: 'mdi-calendar' },
            { i18nLabel: 'nav.reports', path: '/app/reports', icon: 'mdi-file-document-outline' },
        ],
    },
    {
        key: 'lab',
        i18nLabel: 'nav.settings',
        items: [
            { i18nLabel: 'nav.servers', path: '/app/servers', icon: 'mdi-server' },
            { i18nLabel: 'nav.experiments', path: '/app/experiments', icon: 'mdi-flask' },
        ],
    },
];
// const userRoles = computed<Role[]>(() => authStore.user?.roles ?? []);

//const canAccess = (required?: Role[]) => !required || required.length === 0 || required.some((r) => userRoles.value.includes(r));

const visibleSections = computed(
    () => navSections,
    //   navSections
    //     .filter((s) => canAccess(s.roles))
    //     .map((s) => ({ ...s, items: s.items.filter((i) => canAccess(i.roles)) }))
    //     .filter((s) => s.items.length > 0),
);

onMounted(() => {
    isCollapsed.value = localStorage.getItem('isCollapsed') === 'true';
    isDrawerOpen.value = !display.smAndDown.value;
    theme.global.name.value = localStorage.getItem('theme') ?? 'light';
});
</script>

<template>
    <v-app>
        <v-app-bar flat class="border-b mb-7">
            <v-app-bar-title>
                <div v-if="display.smAndDown.value && authStore.accessToken" class="d-flex align-center ga-2">
                    <v-icon @click="handleMainClick">
                        {{ isDrawerOpen ? 'mdi-chevron-left' : 'mdi-chevron-right' }}
                    </v-icon>
                    <div class="cursor-pointer" @click="router.push('/')">OLM</div>
                </div>

                <div v-else class="cursor-pointer" @click="router.push('/')">
                    {{ $t('nav.appName') }}
                </div>
            </v-app-bar-title>
            <v-spacer />
            <div style="display: flex; align-items: center">
                <div class="">
                    <v-btn icon="mdi-theme-light-dark" @click="handleThemeChange" />
                </div>
                <LanguageSelector />
                <UserSelector />
            </div>
        </v-app-bar>
        <v-navigation-drawer
            v-if="authStore.accessToken"
            v-model="isDrawerOpen"
            :rail="isCollapsed"
            :permanent="$vuetify.display.mdAndUp"
            :temporary="$vuetify.display.smAndDown"
        >
            <v-list class="py-0">
                <template v-for="(section, sIndex) in visibleSections" :key="section.key">
                    <!-- <v-divider v-if="sIndex > 0" class="my-0" /> -->

                    <v-list-subheader v-show="!isCollapsed || display.smAndDown.value" class="text-uppercase text-caption">
                        {{ $t(section.i18nLabel) }}
                    </v-list-subheader>

                    <v-list-item v-for="item in section.items" :key="item.path" :to="item.path" class="d-flex align-center py-3">
                        <template #prepend>
                            <v-icon :icon="item.icon" />
                        </template>
                        <span v-show="!isCollapsed || display.smAndDown.value">
                            {{ $t(item.i18nLabel) }}
                        </span>
                    </v-list-item>
                </template>
            </v-list>
            <template #append>
                <div class="d-flex w-100 pa-2" :class="[isCollapsed ? 'justify-center' : 'justify-end', display.smAndDown.value ? '' : 'border-t']">
                    <v-btn icon variant="text" size="small" class="d-none d-md-flex" @click="handleCollapse">
                        <v-icon>
                            {{ isCollapsed ? 'mdi-chevron-right' : 'mdi-chevron-left' }}
                        </v-icon>
                    </v-btn>
                </div>
            </template>
        </v-navigation-drawer>

        <v-main>
            <div class="px-7 mb-5 mt-5">
                <router-view />
            </div>
        </v-main>
    </v-app>
</template>
