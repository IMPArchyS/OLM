<script setup lang="ts">
import { inject } from 'vue'
import type { Ref } from 'vue'
import type { NavItem } from '@/composables/useMainLayout'

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
            'bg-base-300 text-base-content flex justify-center flex-col transition-all duration-300 z-100 shrink-0',
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
                'p-2! border-b border-base-content/10 flex items-center min-h-[88px]',
                sidebarCollapsed && sidebarVisible && windowWidth >= 720
                    ? 'justify-center'
                    : 'justify-between',
            ]"
        >
            <div
                v-show="(!sidebarCollapsed && sidebarVisible) || windowWidth < 720"
                class="text-base font-semibold leading-tight whitespace-nowrap"
            >
                <div class="text-base-content">ONLINE LABORATORY</div>
                <div class="text-base-content/60">MANAGER</div>
            </div>
            <div
                v-show="sidebarCollapsed && sidebarVisible && windowWidth >= 720"
                class="text-base font-semibold whitespace-nowrap"
            >
                <div class="text-base-content">OLM</div>
            </div>
        </div>

        <!-- Navigation -->
        <nav class="flex-1 py-5 overflow-y-auto">
            <!-- Main Navigation -->
            <div class="mb-7">
                <div
                    v-show="(!sidebarCollapsed && sidebarVisible) || windowWidth < 720"
                    class="p-2! font-semibold text-base-content/50 uppercase tracking-wider whitespace-nowrap"
                >
                    LAB
                </div>
                <ul class="p-0">
                    <li v-for="item in navItems" :key="item.id" class="list-none">
                        <button
                            @click="navigate(item.route)"
                            :class="[
                                'flex items-center gap-4 py-1! text-base transition-all border-l-[5px] w-full',
                                sidebarCollapsed && sidebarVisible && windowWidth >= 720
                                    ? 'justify-center'
                                    : 'justify-start',
                                isActiveRoute(item.route)
                                    ? 'bg-base-content/10 border-l-primary text-base-content'
                                    : 'border-l-transparent text-base-content hover:bg-base-content/10',
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
                                {{ item.label }}
                            </span>
                        </button>
                    </li>
                </ul>
            </div>

            <!-- Settings Navigation -->
            <div class="mb-7">
                <div
                    v-show="(!sidebarCollapsed && sidebarVisible) || windowWidth < 720"
                    class="p-2! font-semibold text-base-content/50 uppercase tracking-wider whitespace-nowrap"
                >
                    SETTINGS
                </div>
                <ul class="p-0">
                    <li v-for="item in settingsItems" :key="item.id" class="list-none">
                        <button
                            @click="navigate(item.route)"
                            :class="[
                                'flex items-center gap-4 py-1! text-base transition-all border-l-[5px] w-full',
                                sidebarCollapsed && sidebarVisible && windowWidth >= 720
                                    ? 'justify-center'
                                    : 'justify-start',
                                isActiveRoute(item.route)
                                    ? 'bg-base-content/10 border-l-primary text-base-content'
                                    : 'border-l-transparent text-base-content hover:bg-base-content/10',
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
                                {{ item.label }}
                            </span>
                        </button>
                    </li>
                </ul>
            </div>
        </nav>

        <!-- Footer (collapse toggle - only visible at >= 920px) -->
        <div
            v-if="windowWidth >= 930"
            :class="[
                'border-t border-base-content/10 flex items-center',
                sidebarCollapsed ? 'justify-center p-0' : 'p-5',
            ]"
        >
            <button
                @click="toggleSidebar"
                :class="[
                    'btn btn-ghost',
                    sidebarCollapsed ? 'w-full h-full rounded-none' : 'w-full justify-end',
                ]"
            >
                {{ sidebarCollapsed ? '>' : '<' }}
            </button>
        </div>
    </aside>
    <div
        v-if="sidebarVisible && windowWidth < 720"
        class="fixed inset-0 bg-base-300/40 z-99"
        @click="sidebarVisible = false"
    ></div>
</template>
