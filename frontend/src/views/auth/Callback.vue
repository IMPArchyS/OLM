<script lang="ts" setup>
import { apiClient } from '@/lib/apiClient';
import { useAuthStore } from '@/stores/auth';
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const authStore = useAuthStore();

onMounted(async () => {
    try {
        await authStore.handleOAuthCallback();
        await router.push('/app/dashboard');
    } catch (e) {
        console.error('OAuth callback failed:', e);
        router.push({ name: 'login', params: { error: 'auth_failed' } });
    }
});
</script>

<template>
    <div>Prihlasujem...</div>
</template>
