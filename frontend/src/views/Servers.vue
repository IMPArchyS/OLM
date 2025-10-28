<script setup lang="ts">
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<template>
    <v-card class="mt-5" color="surface-variant">
        <v-card-title>
            {{ t('servers.title') }}
        </v-card-title>
        <v-card-text> </v-card-text>
    </v-card>
</template>
