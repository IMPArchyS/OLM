<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const username = ref('');
const password = ref('');
const isSubmitting = ref(false);
const errorMessage = ref('');
const oauthRedirectPath = '/app/dashboard';

onMounted(async () => {
    await authStore.fetchProviders();

    if (route.params.error === 'auth_failed') {
        errorMessage.value = 'Authentication failed. Please try again.';
    }
});

const handleLogin = async () => {
    if (isSubmitting.value) return;

    isSubmitting.value = true;

    try {
        await authStore.login({
            username: username.value,
            password: password.value,
        });

        await router.push('/app/dashboard');
    } catch (error) {
        console.error('Login failed:', error);
    } finally {
        isSubmitting.value = false;
    }
};

const handleOauthLogin = (provider: string) => {
    authStore.oauthLogin({
        provider,
        redirect: window.location.origin + '/auth/callback',
    });
};
</script>

<template>
    <v-card max-width="400" class="mx-auto mt-5">
        <v-card-title class="text-h5 mb-4">Login</v-card-title>
        <v-card-text v-if="authStore.providers.length > 0">
            <v-btn
                v-for="provider in authStore.providers"
                :key="provider.id"
                @click="handleOauthLogin(provider.name)"
                variant="outlined"
                class="mb-2"
            >
                <template #prepend>
                    <v-img v-if="provider.logo_url" :src="provider.logo_url" width="28" height="28" class="rounded-circle" />
                </template>
                {{ provider.display_name }}
            </v-btn>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-text>
            <v-alert v-if="errorMessage" type="error" class="mb-4" closable @click:close="errorMessage = ''">
                {{ errorMessage }}
            </v-alert>

            <v-form @submit.prevent="handleLogin">
                <v-text-field
                    v-model="username"
                    label="Email"
                    placeholder="Enter email"
                    type="email"
                    variant="outlined"
                    density="comfortable"
                    required
                    :disabled="isSubmitting"
                    class="mb-4"
                />
                <v-text-field
                    v-model="password"
                    label="Password"
                    placeholder="Enter password"
                    type="password"
                    variant="outlined"
                    density="comfortable"
                    required
                    :disabled="isSubmitting"
                    class="mb-4"
                />
                <v-btn type="submit" color="primary" variant="elevated" block class="mt-2" :loading="isSubmitting" :disabled="!username || !password">
                    Login
                </v-btn>
            </v-form>
            <v-divider class="my-4" />
            <v-btn :to="{ name: 'register' }" variant="text" block> Create an account </v-btn>
        </v-card-text>
    </v-card>
</template>
