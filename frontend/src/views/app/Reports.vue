<script setup lang="ts">
import { useExperimentLogs } from '@/composables/useExperimentLogs';
import { useToast } from '@/composables/useToast';
import { useAuthStore } from '@/stores/auth';
import { onMounted } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const authStore = useAuthStore();
const { showError } = useToast();
const { userExperimentLogs, loading, error, fetchExperimentLogsByUser } = useExperimentLogs();

onMounted(async () => {
    const result = await fetchExperimentLogsByUser(authStore.user?.id);
    if (!result.success) {
        showError(result.message || 'Failed');
    }
});
</script>

<template>
    <v-card class="mt-5">
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ t('reports.title') }}</span>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
            <pre>{{ JSON.stringify(userExperimentLogs, null, 2) }}</pre>
        </v-card-text>
    </v-card>
</template>
