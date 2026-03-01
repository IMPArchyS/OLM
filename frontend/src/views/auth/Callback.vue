<script setup>
import { useToast } from '@/composables/useToast';
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

onMounted(async () => {
    try {
        const response = await fetch('/api/auth/session', {
            method: 'POST',
            credentials: 'include',
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            router.push('/');
        } else {
            router.push({ name: 'login', params: { error: 'auth_failed' } });
        }
    } catch (e) {
        router.push({ name: 'login', params: { error: 'auth_failed' } });
    }
});
</script>

<template>
    <div>Prihlasujem...</div>
</template>
