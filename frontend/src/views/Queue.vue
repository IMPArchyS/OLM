<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
    <v-card>
        <v-card-title>
            {{ t('queues.title') }}
        </v-card-title>
        <v-card-text> </v-card-text>
    </v-card>
</template>
