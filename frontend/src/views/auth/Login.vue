<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useI18n } from 'vue-i18n';
import { useToastStore } from '@/stores/toast';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const toast = useToastStore();

const username = ref('');
const password = ref('');
const isSubmitting = ref(false);
const showPassword = ref(false);

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const emailRules = [
    (value: string) => !!value || `${t('auth.email')} ${t('validation.required_male')}`,
    (value: string) => emailRegex.test(value) || t('validation.invalidFormat'),
];

onMounted(async () => {
    await authStore.fetchProviders();

    if (route.params.error === 'auth_failed') {
        toast.error(t('error.auth_failed'));
    }
});

const handleLogin = async () => {
    if (isSubmitting.value) return;

    if (!emailRegex.test(username.value)) {
        toast.error(t('validation.invalidFormat'));
        return;
    }

    isSubmitting.value = true;

    try {
        await authStore.login({ username: username.value, password: password.value });
        await router.push('/app/dashboard');
    } catch (error) {
        toast.error(t('error.login'));
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
        <v-card-title class="text-h5 mb-4">{{ t('auth.login') }}</v-card-title>
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
            <v-form @submit.prevent="handleLogin">
                <v-text-field
                    v-model="username"
                    prepend-inner-icon="mdi-email-outline"
                    :label="$t('auth.email')"
                    type="email"
                    :rules="emailRules"
                    variant="outlined"
                    density="comfortable"
                    required
                    :disabled="isSubmitting"
                    class="mb-4"
                />
                <v-text-field
                    v-model="password"
                    prepend-inner-icon="mdi-lock-outline"
                    :label="$t('auth.password')"
                    :type="showPassword ? 'text' : 'password'"
                    variant="outlined"
                    density="comfortable"
                    :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                    @click:append-inner="showPassword = !showPassword"
                    required
                    :disabled="isSubmitting"
                    class="mb-4"
                />
                <v-btn type="submit" color="primary" variant="elevated" block class="mt-2" :loading="isSubmitting" :disabled="!username || !password">
                    {{ t('auth.login') }}
                </v-btn>
            </v-form>
            <v-divider class="my-4" />
            <v-btn :to="{ name: 'register' }" variant="text" block> {{ t('auth.createAccount') }} </v-btn>
        </v-card-text>
    </v-card>
</template>
