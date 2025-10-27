<script setup lang="ts">
import { useLanguageStore } from '@/stores/language'
import { ref } from 'vue'

const languageStore = useLanguageStore()
const isOpen = ref(false)

const toggleDropdown = () => {
    isOpen.value = !isOpen.value
}

const selectLanguage = (langCode: string) => {
    languageStore.setLanguage(langCode)
    isOpen.value = false
}

// Close dropdown when clicking outside
const closeDropdown = () => {
    isOpen.value = false
}
</script>

<template>
    <div class="relative" v-click-outside="closeDropdown">
        <!-- Language Button -->
        <button @click="toggleDropdown" class="btn btn-ghost gap-2 normal-case" type="button">
            <span class="text-xl">{{ languageStore.currentLanguage.flag }}</span>
            <span class="font-medium">{{ languageStore.currentLanguage.code.toUpperCase() }}</span>
            <svg
                class="w-4 h-4 transition-transform duration-200"
                :class="{ 'rotate-180': isOpen }"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 9l-7 7-7-7"
                />
            </svg>
        </button>

        <!-- Dropdown Menu -->
        <transition
            enter-active-class="transition ease-out duration-200"
            enter-from-class="opacity-0 translate-y-1"
            enter-to-class="opacity-100 translate-y-0"
            leave-active-class="transition ease-in duration-150"
            leave-from-class="opacity-100 translate-y-0"
            leave-to-class="opacity-0 translate-y-1"
        >
            <div
                v-if="isOpen"
                class="absolute right-0 mt-2 rounded-lg shadow-lg bg-base-100 border border-base-300 z-50"
            >
                <ul class="menu p-2">
                    <li v-for="lang in languageStore.languages" :key="lang.code">
                        <button
                            @click="selectLanguage(lang.code)"
                            class="flex items-center gap-3 w-full p-2!"
                            :class="{ active: lang.code === languageStore.currentLanguage.code }"
                        >
                            <span class="text-xl">{{ lang.flag }}</span>
                            <div class="flex flex-col items-start">
                                <span class="font-medium">{{ lang.name }}</span>
                            </div>
                        </button>
                    </li>
                </ul>
            </div>
        </transition>
    </div>
</template>

<style scoped>
/* Additional smooth transitions */
.menu li button {
    transition: all 0.2s ease;
}

.menu li button.active {
    background-color: hsl(var(--p) / 0.1);
    color: hsl(var(--p));
}
</style>
