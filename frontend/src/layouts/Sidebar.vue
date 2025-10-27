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
    <aside
        :class="[
            'bg-slate-600 text-base-content flex justify-center flex-col transition-all duration-300 z-100 shrink-0',
            windowWidth < 720
                ? 'fixed top-0 left-0 h-screen w-64'
                : sidebarVisible
                  ? sidebarCollapsed
                      ? 'w-16'
                      : 'w-64'
                  : 'w-0 overflow-hidden',
            windowWidth < 720 && !sidebarVisible ? '-translate-x-full' : 'translate-x-0',
        ]"
    >
        <!-- Header -->
        <div
            :class="[
                'bg-slate-700 p-2! border-b border-base-content/10 flex items-center min-h-[88px]',
                sidebarCollapsed && sidebarVisible && windowWidth >= 720
                    ? 'justify-center'
                    : 'justify-between',
            ]"
        >
            <div
                v-show="(!sidebarCollapsed && sidebarVisible) || windowWidth < 720"
                class="text-base font-semibold leading-tight whitespace-nowrap"
            >
                <div class="text-white">ONLINE LABORATORY</div>
                <div class="text-gray-200">MANAGER</div>
            </div>
            <div
                v-show="sidebarCollapsed && sidebarVisible && windowWidth >= 720"
                class="text-base font-semibold whitespace-nowrap"
            >
                <div class="text-white">OLM</div>
            </div>
        </div>

        <!-- Navigation -->
        <nav class="flex-1 py-5 overflow-y-auto">
            <!-- Main Navigation -->
            <div class="mb-7">
                <div
                    v-show="(!sidebarCollapsed && sidebarVisible) || windowWidth < 720"
                    class="p-2! font-semibold text-white uppercase tracking-wider whitespace-nowrap"
                >
                    {{ t('nav.lab') }}
                </div>
                <ul class="p-0">
                    <li v-for="item in navItems" :key="item.id" class="list-none">
                        <button
                            @click="navigate(item.route)"
                            :class="[
                                'clickable flex items-center gap-4 py-1! px-1.5! transition-all w-full',
                                sidebarCollapsed && sidebarVisible && windowWidth >= 720
                                    ? 'justify-center'
                                    : 'justify-start',
                                isActiveRoute(item.route)
                                    ? 'bg-white/20 border-l-primary text-white'
                                    : 'border-l-transparent text-white/60 hover:bg-white/20',
                            ]"
                            :title="sidebarCollapsed && windowWidth >= 720 ? item.label : ''"
                        >
                            <span class="text-2xl flex items-center justify-center min-w-6">{{
                                item.icon
                            }}</span>
                            <span
                                v-show="(!sidebarCollapsed && sidebarVisible) || windowWidth < 720"
                                class="whitespace-nowrap overflow-hidden text-ellipsis"
                            >
                                {{ t('nav.' + item.label) }}
                            </span>
                        </button>
                    </li>
                </ul>
            </div>

            <!-- Settings Navigation -->
            <div class="mb-7">
                <div
                    v-show="(!sidebarCollapsed && sidebarVisible) || windowWidth < 720"
                    class="p-2! font-semibold text-white uppercase tracking-wider whitespace-nowrap"
                >
                    {{ t('nav.settings') }}
                </div>
                <ul class="p-0">
                    <li v-for="item in settingsItems" :key="item.id" class="list-none">
                        <button
                            @click="navigate(item.route)"
                            :class="[
                                'clickable flex items-center gap-4 py-1! px-1.5! transition-all w-full',
                                sidebarCollapsed && sidebarVisible && windowWidth >= 720
                                    ? 'justify-center'
                                    : 'justify-start',
                                isActiveRoute(item.route)
                                    ? 'bg-white/20 border-l-primary text-white'
                                    : 'border-l-transparent text-white/60 hover:bg-white/20',
                            ]"
                            :title="sidebarCollapsed && windowWidth >= 720 ? item.label : ''"
                        >
                            <span class="text-2xl flex items-center justify-center min-w-6">{{
                                item.icon
                            }}</span>
                            <span
                                v-show="(!sidebarCollapsed && sidebarVisible) || windowWidth < 720"
                                class="whitespace-nowrap overflow-hidden text-ellipsis"
                            >
                                {{ t('nav.' + item.label) }}
                            </span>
                        </button>
                    </li>
                </ul>
            </div>
        </nav>

        <!-- Footer (collapse toggle - only visible at >= 920px) -->
        <div
            v-if="windowWidth >= 930"
            :class="['bg-slate-700 flex items-center', sidebarCollapsed ? 'p-0' : '']"
        >
            <button
                @click="toggleSidebar"
                :class="[
                    'clickable flex items-center gap-4 py-1! transition-all w-full text-white/60 hover:text-white hover:bg-black/20 border-l-transparent',
                    sidebarCollapsed ? 'justify-center h-full rounded-none' : 'justify-end pr-4!',
                ]"
            >
                <span
                    class="text-2xl flex items-center justify-center min-w-6 transition-transform duration-300"
                >
                    {{ sidebarCollapsed ? '>' : '<' }}
                </span>
            </button>
        </div>
    </aside>
    <div
        v-if="sidebarVisible && windowWidth < 720"
        class="fixed inset-0 bg-base-300/40 z-99"
        @click="sidebarVisible = false"
    ></div>
</template>
