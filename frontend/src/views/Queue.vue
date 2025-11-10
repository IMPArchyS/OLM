<script setup lang="ts">
import ExperimentSelector from '@/components/ExperimentSelector.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
    <v-card class="mt-5">
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ t('queues.title') }}</span>
        </v-card-title>
        <v-card-text class="mt-5">
            <ExperimentSelector fixed-command="start" />
        </v-card-text>
    </v-card>
</template>
