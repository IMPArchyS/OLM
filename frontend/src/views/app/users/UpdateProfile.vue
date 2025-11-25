<script setup lang="ts">
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>
<template>
    <v-card class="mt-5">
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ t('actions.update') }}</span>
        </v-card-title>
        <v-card-text class="mt-5">
            <v-form>
                <v-text-field
                    :label="t('auth.username')"
                    type="text"
                    class="mb-4"
                    variant="outlined"
                    density="comfortable"
                ></v-text-field>
                <v-text-field
                    :label="t('auth.email')"
                    type="email"
                    class="mb-4"
                    variant="outlined"
                    density="comfortable"
                ></v-text-field>
                <div class="d-flex justify-center">
                    <v-btn color="primary" class="w-3" type="submit">{{ t('actions.save') }}</v-btn>
                </div>
            </v-form>
        </v-card-text>
    </v-card>
</template>
