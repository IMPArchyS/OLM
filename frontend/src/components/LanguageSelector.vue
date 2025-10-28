<script setup lang="ts">
import { useLanguageStore } from '@/stores/language'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const languageStore = useLanguageStore()
const isOpen = ref(false)
const { locale } = useI18n()

const selectLanguage = (langCode: string) => {
    languageStore.setLanguage(langCode)
    locale.value = langCode // Update i18n locale
    isOpen.value = false
}

// Watch for language changes from store and update i18n
watch(
    () => languageStore.currentLanguage.code,
    (newCode) => {
        locale.value = newCode
    },
)
</script>

<template>
    <v-menu v-model="isOpen" :close-on-content-click="false">
        <template v-slot:activator="{ props }">
            <v-btn v-bind="props" variant="text">
                <span style="font-size: 20px; margin-right: 8px">
                    {{ languageStore.currentLanguage.flag }}
                </span>
                <span style="font-weight: 500">
                    {{ languageStore.currentLanguage.code.toUpperCase() }}
                </span>
                <v-icon
                    :style="{
                        transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.2s',
                    }"
                >
                    mdi-chevron-down
                </v-icon>
            </v-btn>
        </template>

        <v-list>
            <v-list-item
                v-for="lang in languageStore.languages"
                :key="lang.code"
                @click="selectLanguage(lang.code)"
                :active="lang.code === languageStore.currentLanguage.code"
            >
                <template v-slot:prepend>
                    <span style="font-size: 20px; margin-right: 12px">{{ lang.flag }}</span>
                </template>
                <v-list-item-title>{{ lang.name }}</v-list-item-title>
            </v-list-item>
        </v-list>
    </v-menu>
</template>
