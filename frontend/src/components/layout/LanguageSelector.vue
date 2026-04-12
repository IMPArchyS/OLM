<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useLocale } from 'vuetify';

const isOpen = ref(false);
const { locale } = useI18n();
const { current } = useLocale();

const langOptions = [
    { label: 'SK', key: 'sk' },
    { label: 'EN', key: 'en' },
];

const handleLangChange = (targetLangKey: string) => {
    localStorage.setItem('locale', targetLangKey);
    current.value = targetLangKey;
    locale.value = targetLangKey;
};
</script>

<template>
    <v-menu v-model="isOpen" :close-on-content-click="false">
        <template v-slot:activator="{ props }">
            <v-btn v-bind="props" variant="text">
                <span style="font-weight: 500">
                    {{ current.toUpperCase() }}
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
            <v-list-item v-for="lang in langOptions" :key="lang.key" @click="handleLangChange(lang.key)" :active="lang.key === current">
                <v-list-item-title>{{ lang.label }}</v-list-item-title>
            </v-list-item>
        </v-list>
    </v-menu>
</template>
