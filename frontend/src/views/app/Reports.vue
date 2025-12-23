<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
</script>

<template>
    <v-card class="mt-5">
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ t('reports.title') }}</span>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text> </v-card-text>
    </v-card>
</template>
