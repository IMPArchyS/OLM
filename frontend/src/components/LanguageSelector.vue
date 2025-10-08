<script setup lang="ts">
import { ref } from 'vue'

interface Language {
    code: string
    name: string
    flag: string
}

const languages: Language[] = [
    { code: 'sk', name: 'Slovenský', flag: '🇸🇰' },
    { code: 'en', name: 'English', flag: '🇬🇧' },
    // add more here later
]

const selected = ref(languages[0])
const open = ref(false)

const toggleDropdown = () => {
    open.value = !open.value
}

const selectLanguage = (lang: Language) => {
    selected.value = lang
    open.value = false
    // future: add i18n locale switch here
}
</script>

<template>
    <div class="lang-selector">
        <button class="lang-btn" @click="toggleDropdown">
            <span class="flag">{{ selected?.flag }}</span>
            <span class="arrow">▾</span>
        </button>

        <div v-if="open" class="lang-dropdown">
            <button
                v-for="lang in languages"
                :key="lang.code"
                @click="selectLanguage(lang)"
                class="lang-option"
            >
                <span class="flag">{{ lang.flag }}</span>
                <span>{{ lang.name }}</span>
            </button>
        </div>
    </div>
</template>

<style scoped>
.lang-selector {
    position: relative;
    display: inline-block;
}

.lang-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background: white;
    cursor: pointer;
    transition: background 0.2s;
}

.lang-btn:hover {
    background: #f9fafb;
}

.flag {
    font-size: 1.2rem;
}

.arrow {
    margin-left: 0.25rem;
    font-size: 0.7rem;
}

.lang-dropdown {
    position: absolute;
    top: 120%;
    left: 0;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    z-index: 50;
    min-width: 160px;
}

.lang-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.6rem 1rem;
    width: 100%;
    background: white;
    border: none;
    cursor: pointer;
    transition: background 0.2s;
}

.lang-option:hover {
    background: #f3f4f6;
}
</style>
