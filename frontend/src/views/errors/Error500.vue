<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
    <v-container class="fill-height bg-grey-lighten-4">
        <v-row justify="center">
            <v-col
                cols="12"
                class="d-flex flex-column flex-sm-row justify-center align-center text-center text-sm-left"
            >
                <h1 class="text-h1 me-sm-8">500</h1>
                <div>
                    <h4 class="text-h4 pt-2">{{ t('page500.title') }}</h4>
                    <p class="text-medium-emphasis">{{ t('page500.description') }}</p>
                    <v-btn :to="'/'">{{ t('page500.button') }}</v-btn>
                </div>
            </v-col>
        </v-row>
    </v-container>
</template>
