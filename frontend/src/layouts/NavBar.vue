<script setup lang="ts">
import LanguageSelector from '@/components/LanguageSelector.vue'
import ThemeSelector from '@/components/ThemeSelector.vue'
import UserSelector from '@/components/UserSelector.vue'
import { inject, computed } from 'vue'
import { useRoute } from 'vue-router'
import type { Ref } from 'vue'

interface MainLayoutContext {
    toggleSidebarVisibility: () => void
}

const { toggleSidebarVisibility } = inject<MainLayoutContext>('mainLayout')!
const route = useRoute()

// Show hamburger menu only on specific routes
const showMenuButton = computed(() => {
    // Option 3: Show on all routes except auth
    return !route.path.startsWith('/auth')
})
</script>

<template>
    <header
        class="bg-base-200 border-b border-base-content/10 px-7 py-5 mb-7! flex items-center justify-between"
    >
        <div class="flex items-center gap-5">
            <button
                v-if="showMenuButton"
                @click="toggleSidebarVisibility"
                class="btn btn-ghost text-2xl"
            >
                ☰
            </button>
        </div>
        <div class="flex items-center gap-5">
            <ThemeSelector />
            <LanguageSelector />
            <UserSelector />
        </div>
    </header>
</template>
