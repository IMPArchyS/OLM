<script setup lang="ts">
import LanguageSelector from '@/components/layout/LanguageSelector.vue';
import UserSelector from '@/components/layout/UserSelector.vue';
import { inject, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useTheme } from 'vuetify';

interface MainLayoutContext {
    toggleSidebarVisibility: () => void;
}

const { toggleSidebarVisibility } = inject<MainLayoutContext>('mainLayout')!;
const route = useRoute();
const theme = useTheme();

// Show hamburger menu only on specific routes
const showMenuButton = computed(() => {
    // Option 3: Show on all routes except auth
    return !route.path.startsWith('/auth');
});

const handleThemeChange = () => {
    localStorage.setItem('theme', theme.global.current.value.dark ? 'light' : 'dark');
    theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark';
};
</script>

<template>
    <v-app-bar flat class="border-b mb-7 px-7">
        <template v-slot:prepend>
            <v-btn v-if="showMenuButton" @click="toggleSidebarVisibility" icon variant="text" size="large">
                <span style="font-size: 24px">☰</span>
            </v-btn>
        </template>

        <v-spacer />

        <div style="display: flex; align-items: center">
            <div class="">
                <v-btn icon="mdi-theme-light-dark" @click="handleThemeChange" />
            </div>
            <LanguageSelector />
            <UserSelector />
        </div>
    </v-app-bar>
</template>
