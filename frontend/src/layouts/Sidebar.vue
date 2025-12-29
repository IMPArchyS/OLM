<script setup lang="ts">
import { inject, computed } from 'vue';
import type { Ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();

interface MainLayoutContext {
    sidebarCollapsed: Ref<boolean>;
    sidebarVisible: Ref<boolean>;
    windowWidth: Ref<number>;
    toggleSidebar: () => void;
}

const { sidebarCollapsed, sidebarVisible, windowWidth, toggleSidebar } =
    inject<MainLayoutContext>('mainLayout')!;

const isActiveRoute = (routePath: string) => {
    // For servers and schemas, check if current route starts with the path
    if (routePath === '/app/servers' || routePath === '/app/schemas') {
        return route.path.startsWith(routePath);
    }
    return route.path === routePath;
};
const navigate = (routePath: string) => router.push(routePath);

// Computed for responsive behavior
const isCollapsed = computed(() => sidebarCollapsed.value && windowWidth.value >= 720);
const showLabels = computed(() => !isCollapsed.value);
</script>

<template>
    <v-navigation-drawer
        v-model="sidebarVisible"
        :width="isCollapsed ? 80 : 280"
        :temporary="windowWidth < 1280"
        :permanent="windowWidth >= 1280"
        color="rgb(71, 85, 105)"
    >
        <div style="display: flex; flex-direction: column; height: 100vh">
            <!-- Header -->
            <v-sheet
                color="rgb(51, 65, 85)"
                class="pa-4 d-flex align-center shrink-0"
                :class="isCollapsed ? 'justify-center' : 'justify-space-between'"
                height="88"
            >
                <div v-if="showLabels" class="text-subtitle-1 font-weight-medium">
                    <div class="text-white">ONLINE LABORATORY</div>
                    <div style="color: rgb(229, 231, 235)">MANAGER</div>
                </div>
                <div v-else class="text-subtitle-1 font-weight-medium text-white">OLM</div>
            </v-sheet>

            <v-divider color="rgb(51, 65, 85)" />

            <!-- Navigation Content -->
            <div style="flex: 1; overflow-y: auto; padding: 20px 0">
                <!-- Main Navigation -->
                <div class="mb-6">
                    <div
                        v-if="showLabels"
                        class="px-4 mb-2 text-caption font-weight-medium text-uppercase text-white"
                        style="letter-spacing: 0.05em"
                    >
                        {{ t('nav.lab') }}
                    </div>

                    <!-- Dashboard -->
                    <div
                        v-if="isCollapsed"
                        @click="navigate('/app/dashboard')"
                        class="nav-item-collapsed"
                        :class="{ active: isActiveRoute('/app/dashboard') }"
                    >
                        <v-icon icon="mdi-view-dashboard" size="24" />
                    </div>
                    <div
                        v-else
                        @click="navigate('/app/dashboard')"
                        class="nav-item-expanded"
                        :class="{ active: isActiveRoute('/app/dashboard') }"
                    >
                        <v-icon icon="mdi-view-dashboard" size="24" />
                        <span class="ml-4">{{ t('nav.dashboard') }}</span>
                    </div>

                    <!-- Queue -->
                    <div
                        v-if="isCollapsed"
                        @click="navigate('/app/queue')"
                        class="nav-item-collapsed"
                        :class="{ active: isActiveRoute('/app/queue') }"
                    >
                        <v-icon icon="mdi-clock-outline" size="24" />
                    </div>
                    <div
                        v-else
                        @click="navigate('/app/queue')"
                        class="nav-item-expanded"
                        :class="{ active: isActiveRoute('/app/queue') }"
                    >
                        <v-icon icon="mdi-clock-outline" size="24" />
                        <span class="ml-4">{{ t('nav.queue_experiments') }}</span>
                    </div>

                    <!-- Reservations -->
                    <div
                        v-if="isCollapsed"
                        @click="navigate('/app/reservations')"
                        class="nav-item-collapsed"
                        :class="{ active: isActiveRoute('/app/reservations') }"
                    >
                        <v-icon icon="mdi-calendar-clock" size="24" />
                    </div>
                    <div
                        v-else
                        @click="navigate('/app/reservations')"
                        class="nav-item-expanded"
                        :class="{ active: isActiveRoute('/app/reservations') }"
                    >
                        <v-icon icon="mdi-calendar-clock" size="24" />
                        <span class="ml-4">{{ t('nav.reservations') }}</span>
                    </div>

                    <!-- Reports -->
                    <div
                        v-if="isCollapsed"
                        @click="navigate('/app/reports')"
                        class="nav-item-collapsed"
                        :class="{ active: isActiveRoute('/app/reports') }"
                    >
                        <v-icon icon="mdi-file-document-outline" size="24" />
                    </div>
                    <div
                        v-else
                        @click="navigate('/app/reports')"
                        class="nav-item-expanded"
                        :class="{ active: isActiveRoute('/app/reports') }"
                    >
                        <v-icon icon="mdi-file-document-outline" size="24" />
                        <span class="ml-4">{{ t('nav.reports') }}</span>
                    </div>
                </div>

                <!-- Settings Navigation -->
                <div>
                    <div
                        v-if="showLabels"
                        class="px-4 mb-2 text-caption font-weight-medium text-uppercase text-white"
                        style="letter-spacing: 0.05em"
                    >
                        {{ t('nav.settings') }}
                    </div>

                    <!-- Servers -->
                    <div
                        v-if="isCollapsed"
                        @click="navigate('/app/servers')"
                        class="nav-item-collapsed"
                        :class="{ active: isActiveRoute('/app/servers') }"
                    >
                        <v-icon icon="mdi-server" size="24" />
                    </div>
                    <div
                        v-else
                        @click="navigate('/app/servers')"
                        class="nav-item-expanded"
                        :class="{ active: isActiveRoute('/app/servers') }"
                    >
                        <v-icon icon="mdi-server" size="24" />
                        <span class="ml-4">{{ t('nav.servers') }}</span>
                    </div>

                    <!-- Schemas -->
                    <div
                        v-if="isCollapsed"
                        @click="navigate('/app/schemas')"
                        class="nav-item-collapsed"
                        :class="{ active: isActiveRoute('/app/schemas') }"
                    >
                        <v-icon icon="mdi-clipboard-list-outline" size="24" />
                    </div>
                    <div
                        v-else
                        @click="navigate('/app/schemas')"
                        class="nav-item-expanded"
                        :class="{ active: isActiveRoute('/app/schemas') }"
                    >
                        <v-icon icon="mdi-clipboard-list-outline" size="24" />
                        <span class="ml-4">{{ t('nav.schemas') }}</span>
                    </div>
                </div>
            </div>

            <!-- Footer Toggle (only visible at >= 930px) -->
            <v-sheet v-if="windowWidth >= 930" color="rgb(51, 65, 85)" style="flex-shrink: 0">
                <v-divider color="rgb(51, 65, 85)" />
                <div
                    @click="toggleSidebar"
                    class="toggle-button"
                    :style="{
                        justifyContent: isCollapsed ? 'center' : 'flex-end',
                        paddingRight: isCollapsed ? '0' : '16px',
                    }"
                >
                    <v-icon :icon="isCollapsed ? 'mdi-chevron-right' : 'mdi-chevron-left'" />
                </div>
            </v-sheet>
        </div>
    </v-navigation-drawer>
</template>

<style scoped>
.nav-item-collapsed {
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: rgba(255, 255, 255, 0.6);
    border-left: 3px solid transparent;
    margin: 4px 0;
    transition: all 0.2s;
}

.nav-item-collapsed:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: rgba(255, 255, 255, 0.8);
}

.nav-item-collapsed.active {
    background-color: rgba(255, 255, 255, 0.1);
    border-left-color: rgb(var(--v-theme-primary));
    color: white;
}

.nav-item-expanded {
    height: 48px;
    display: flex;
    align-items: center;
    cursor: pointer;
    color: rgba(255, 255, 255, 0.6);
    border-left: 3px solid transparent;
    margin: 4px 8px;
    padding: 0 12px;
    border-radius: 4px;
    transition: all 0.2s;
}

.nav-item-expanded:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: rgba(255, 255, 255, 0.8);
}

.nav-item-expanded.active {
    background-color: rgba(255, 255, 255, 0.1);
    border-left-color: rgb(var(--v-theme-primary));
    color: white;
}

.toggle-button {
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: rgba(255, 255, 255, 0.6);
    transition: all 0.2s;
}

.toggle-button:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: rgba(255, 255, 255, 0.8);
}
</style>
