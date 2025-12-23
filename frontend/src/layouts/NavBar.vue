<script setup lang="ts">
import LanguageSelector from '@/components/LanguageSelector.vue';
import ThemeSelector from '@/components/ThemeSelector.vue';
import UserSelector from '@/components/UserSelector.vue';
import { inject, computed } from 'vue';
import { useRoute } from 'vue-router';
import type { Ref } from 'vue';

interface MainLayoutContext {
    toggleSidebarVisibility: () => void;
}

const { toggleSidebarVisibility } = inject<MainLayoutContext>('mainLayout')!;
const route = useRoute();

// Show hamburger menu only on specific routes
const showMenuButton = computed(() => {
    // Option 3: Show on all routes except auth
    return !route.path.startsWith('/auth');
});
</script>

<template>
    <v-app-bar flat class="border-b mb-7 px-7">
        <template v-slot:prepend>
            <v-btn
                v-if="showMenuButton"
                @click="toggleSidebarVisibility"
                icon
                variant="text"
                size="large"
            >
                <span style="font-size: 24px">☰</span>
            </v-btn>
        </template>

        <v-spacer />

        <div style="display: flex; align-items: center">
            <ThemeSelector />
            <LanguageSelector />
            <UserSelector />
        </div>
    </v-app-bar>
</template>
