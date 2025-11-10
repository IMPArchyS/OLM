<script setup lang="ts">
import ExperimentSelector from '@/components/ExperimentSelector.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
    <v-card class="mt-5" color="surface-variant">
        <v-card-title>
            {{ t('queues.title') }}
        </v-card-title>
        <v-card-text>
            <ExperimentSelector fixed-command="start" />
        </v-card-text>
    </v-card>
</template>
