<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useI18n } from 'vue-i18n';
import { useToastStore } from '@/stores/toast';
import rules from '@/utils/validationRules';

const router = useRouter();
const authStore = useAuthStore();
const toast = useToastStore();
const { t } = useI18n();

const username = ref('');
const name = ref('');
const password = ref('');
const confirmPassword = ref('');
const showPassword = ref(false);
const isSubmitting = ref(false);

const handleRegister = async () => {
    if (isSubmitting.value) return;

    if (password.value !== confirmPassword.value) {
        toast.error(t('error.matchPassword'));
        return;
    }
    isSubmitting.value = true;

    try {
        await authStore.register({ name: name.value, username: username.value, password: password.value });
        await router.push('/app/dashboard');
    } catch (error) {
        toast.error(t('error.register'));
    } finally {
        isSubmitting.value = false;
    }
};
</script>

<template>
    <v-card max-width="500" class="mx-auto" elevation="4">
        <v-card-title class="bg-card-title mb-4">
            <v-icon icon="mdi-account" class="mr-2" />
            <span>{{ t('auth.register') }}</span>
        </v-card-title>
        <v-card-text>
            <v-form @submit.prevent="handleRegister" class="d-flex flex-column ga-4">
                <v-text-field
                    v-model="name"
                    prepend-inner-icon="mdi-rename"
                    :label="t('auth.username')"
                    :rules="[rules.requiredFor(t('auth.username'))]"
                    variant="outlined"
                    density="comfortable"
                    required
                    :disabled="isSubmitting"
                />
                <v-text-field
                    v-model="username"
                    prepend-inner-icon="mdi-email-outline"
                    :label="t('auth.email')"
                    type="email"
                    :rules="[rules.validEmail, rules.requiredFor(t('auth.email'))]"
                    variant="outlined"
                    density="comfortable"
                    required
                    :disabled="isSubmitting"
                />
                <v-text-field
                    v-model="password"
                    prepend-inner-icon="mdi-lock-outline"
                    :label="t('auth.password')"
                    :type="showPassword ? 'text' : 'password'"
                    :rules="[rules.requiredFor(t('auth.password'))]"
                    variant="outlined"
                    density="comfortable"
                    :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                    @click:append-inner="showPassword = !showPassword"
                    required
                    :disabled="isSubmitting"
                />
                <v-text-field
                    v-model="confirmPassword"
                    prepend-inner-icon="mdi-repeat-variant"
                    :label="t('auth.confirmPassword')"
                    :type="showPassword ? 'text' : 'password'"
                    :rules="[rules.requiredFor(t('auth.confirmPassword'))]"
                    variant="outlined"
                    density="comfortable"
                    required
                    :disabled="isSubmitting"
                />
                <v-btn
                    prepend-icon="mdi-account-plus"
                    type="submit"
                    color="primary"
                    variant="elevated"
                    block
                    :loading="isSubmitting"
                    :disabled="!username || !name || !password || !confirmPassword"
                >
                    {{ t('auth.register') }}
                </v-btn>
            </v-form>
            <v-divider class="my-4" />
            <v-btn :to="{ name: 'login' }" variant="text" block> {{ t('auth.alreadyAccount') }} </v-btn>
        </v-card-text>
    </v-card>
</template>
