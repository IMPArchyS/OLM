<script setup lang="ts">
import LanguageSelector from '@/components/LanguageSelector.vue'
import ThemeSelector from '@/components/ThemeSelector.vue'
import UserSelector from '@/components/UserSelector.vue'
import { useMainLayout } from '@/composables/useMainLayout'

const {
    sidebarCollapsed,
    sidebarVisible,
    windowWidth,
    navItems,
    settingsItems,
    isActiveRoute,
    navigate,
    toggleSidebar,
    toggleSidebarVisibility,
} = useMainLayout()
</script>

<template>
    <div class="flex h-screen overflow-hidden">
        <!-- Sidebar -->
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
                    'p-5 border-b border-base-content/10 flex items-center min-h-[88px]',
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
                        class="px-5 mb-2 text-xs font-semibold text-base-content/50 uppercase tracking-wider whitespace-nowrap"
                    >
                        LAB
                    </div>
                    <ul class="p-0">
                        <li v-for="item in navItems" :key="item.id" class="list-none">
                            <button
                                @click="navigate(item.route)"
                                :class="[
                                    'flex items-center gap-4 px-5 py-4 text-base transition-all border-l-[5px] w-full',
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
                                    v-show="
                                        (!sidebarCollapsed && sidebarVisible) || windowWidth < 720
                                    "
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
                        class="px-5 mb-2 text-xs font-semibold text-base-content/50 uppercase tracking-wider whitespace-nowrap"
                    >
                        SETTINGS
                    </div>
                    <ul class="p-0">
                        <li v-for="item in settingsItems" :key="item.id" class="list-none">
                            <button
                                @click="navigate(item.route)"
                                :class="[
                                    'flex items-center gap-4 px-5 py-4 text-base transition-all border-l-[5px] w-full',
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
                                    v-show="
                                        (!sidebarCollapsed && sidebarVisible) || windowWidth < 720
                                    "
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
                v-if="windowWidth >= 920"
                :class="[
                    'border-t border-base-content/10 flex items-center min-h-[88px]',
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

        <!-- Overlay for mobile -->
        <div
            v-if="sidebarVisible && windowWidth < 720"
            class="fixed inset-0 bg-base-300/40 z-99"
            @click="sidebarVisible = false"
        ></div>

        <!-- Main Content Area -->
        <div class="flex-1 flex flex-col overflow-hidden bg-base-100">
            <!-- Top Bar -->
            <header
                class="bg-base-200 border-b border-base-content/10 px-7 py-5 flex items-center justify-between"
            >
                <div class="flex items-center gap-5">
                    <button @click="toggleSidebarVisibility" class="btn btn-ghost text-2xl">
                        ☰
                    </button>
                </div>
                <div class="flex items-center gap-5">
                    <ThemeSelector />
                    <LanguageSelector />
                    <UserSelector />
                </div>
            </header>

            <!-- Content Area -->
            <main class="flex-1 p-7 overflow-y-auto">
                <router-view />
            </main>
        </div>
    </div>
</template>
