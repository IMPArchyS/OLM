<script setup lang="ts">
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<template>
    <div class="card bg-base-300! p-0! rounded-2xl!">
        <div class="card-header">
            <h2 class="text-xl font-semibold py-2.5! px-2.5!">{{ t('schemas.title') }}</h2>
        </div>
        <div class="card-body bg-base-200 rounded-b-2xl! px-2.5! pt-2! pb-4!"></div>
    </div>
</template>
