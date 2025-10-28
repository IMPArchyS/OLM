<script setup lang="ts">
import { inject } from 'vue'
import type { Ref } from 'vue'
import type { NavItem } from '@/composables/useMainLayout'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface MainLayoutContext {
    sidebarCollapsed: Ref<boolean>
    sidebarVisible: Ref<boolean>
    windowWidth: Ref<number>
    navItems: NavItem[]
    settingsItems: NavItem[]
    isActiveRoute: (route: string) => boolean
    navigate: (route: string) => void
    toggleSidebar: () => void
    toggleSidebarVisibility: () => void
}

const {
    sidebarCollapsed,
    sidebarVisible,
    windowWidth,
    navItems,
    settingsItems,
    isActiveRoute,
    navigate,
    toggleSidebar,
} = inject<MainLayoutContext>('mainLayout')!
</script>

<template>
    <v-navigation-drawer
        v-model="sidebarVisible"
        :rail="sidebarCollapsed && windowWidth >= 720"
        :temporary="windowWidth < 720"
        color="rgb(71, 85, 105)"
        class="text-white"
    >
        <!-- Header -->
        <v-sheet
            color="rgb(51, 65, 85)"
            class="pa-2 border-b"
            style="min-height: 88px; display: flex; align-items: center"
            :style="{
                justifyContent:
                    sidebarCollapsed && sidebarVisible && windowWidth >= 720
                        ? 'center'
                        : 'space-between',
            }"
        >
            <div
                v-show="(!sidebarCollapsed && sidebarVisible) || windowWidth < 720"
                class="text-base font-weight-medium"
                style="line-height: 1.2; white-space: nowrap"
            >
                <div style="color: white">ONLINE LABORATORY</div>
                <div style="color: rgb(229, 231, 235)">MANAGER</div>
            </div>
            <div
                v-show="sidebarCollapsed && sidebarVisible && windowWidth >= 720"
                class="text-base font-weight-medium"
                style="white-space: nowrap"
            >
                <div style="color: white">OLM</div>
            </div>
        </v-sheet>

        <!-- Navigation -->
        <div style="flex: 1; padding: 20px 0; overflow-y: auto">
            <!-- Main Navigation -->
            <div class="mb-7">
                <div
                    v-show="(!sidebarCollapsed && sidebarVisible) || windowWidth < 720"
                    class="pa-2 font-weight-medium text-uppercase"
                    style="color: white; letter-spacing: 0.05em; white-space: nowrap"
                >
                    {{ t('nav.lab') }}
                </div>
                <v-list density="compact" nav color="transparent">
                    <v-list-item
                        v-for="item in navItems"
                        :key="item.id"
                        @click="navigate(item.route)"
                        :active="isActiveRoute(item.route)"
                        :title="sidebarCollapsed && windowWidth >= 720 ? item.label : ''"
                        class="px-1.5 py-1"
                        style="border-left: 3px solid transparent"
                        :style="{
                            justifyContent:
                                sidebarCollapsed && sidebarVisible && windowWidth >= 720
                                    ? 'center'
                                    : 'flex-start',
                            backgroundColor: isActiveRoute(item.route)
                                ? 'rgba(255,255,255,0.2)'
                                : 'transparent',
                            borderLeftColor: isActiveRoute(item.route)
                                ? 'rgb(var(--v-theme-primary))'
                                : 'transparent',
                            color: isActiveRoute(item.route) ? 'white' : 'rgba(255,255,255,0.6)',
                        }"
                    >
                        <template v-slot:prepend>
                            <span
                                style="
                                    font-size: 24px;
                                    min-width: 24px;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                "
                            >
                                {{ item.icon }}
                            </span>
                        </template>
                        <v-list-item-title
                            v-show="(!sidebarCollapsed && sidebarVisible) || windowWidth < 720"
                            style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis"
                        >
                            {{ t('nav.' + item.label) }}
                        </v-list-item-title>
                    </v-list-item>
                </v-list>
            </div>

            <!-- Settings Navigation -->
            <div class="mb-7">
                <div
                    v-show="(!sidebarCollapsed && sidebarVisible) || windowWidth < 720"
                    class="pa-2 font-weight-medium text-uppercase"
                    style="color: white; letter-spacing: 0.05em; white-space: nowrap"
                >
                    {{ t('nav.settings') }}
                </div>
                <v-list density="compact" nav color="transparent">
                    <v-list-item
                        v-for="item in settingsItems"
                        :key="item.id"
                        @click="navigate(item.route)"
                        :active="isActiveRoute(item.route)"
                        :title="sidebarCollapsed && windowWidth >= 720 ? item.label : ''"
                        class="px-1.5 py-1"
                        style="border-left: 3px solid transparent"
                        :style="{
                            justifyContent:
                                sidebarCollapsed && sidebarVisible && windowWidth >= 720
                                    ? 'center'
                                    : 'flex-start',
                            backgroundColor: isActiveRoute(item.route)
                                ? 'rgba(255,255,255,0.2)'
                                : 'transparent',
                            borderLeftColor: isActiveRoute(item.route)
                                ? 'rgb(var(--v-theme-primary))'
                                : 'transparent',
                            color: isActiveRoute(item.route) ? 'white' : 'rgba(255,255,255,0.6)',
                        }"
                    >
                        <template v-slot:prepend>
                            <span
                                style="
                                    font-size: 24px;
                                    min-width: 24px;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                "
                            >
                                {{ item.icon }}
                            </span>
                        </template>
                        <v-list-item-title
                            v-show="(!sidebarCollapsed && sidebarVisible) || windowWidth < 720"
                            style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis"
                        >
                            {{ t('nav.' + item.label) }}
                        </v-list-item-title>
                    </v-list-item>
                </v-list>
            </div>
        </div>

        <!-- Footer (collapse toggle - only visible at >= 930px) -->
        <v-sheet
            v-if="windowWidth >= 930"
            color="rgb(51, 65, 85)"
            :class="sidebarCollapsed ? 'pa-0' : ''"
        >
            <v-btn
                @click="toggleSidebar"
                variant="text"
                block
                :class="sidebarCollapsed ? 'rounded-0' : 'justify-end pr-4'"
                style="color: rgba(255, 255, 255, 0.6); height: auto"
            >
                <span class="text-2xl" style="min-width: 24px; transition: transform 0.3s">
                    {{ sidebarCollapsed ? '>' : '<' }}
                </span>
            </v-btn>
        </v-sheet>
    </v-navigation-drawer>
</template>
