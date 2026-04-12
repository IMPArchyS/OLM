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
    <v-card max-width="400" class="mx-auto mt-5">
        <v-card-title class="text-h5 mb-4">{{ t('auth.register') }}</v-card-title>
        <v-divider></v-divider>
        <v-card-text>
            <v-form @submit.prevent="handleRegister">
                <v-text-field
                    v-model="name"
                    prepend-inner-icon="mdi-rename"
                    :label="$t('auth.name')"
                    :rules="[rules.requiredFor(t('auth.name'))]"
                    variant="outlined"
                    density="comfortable"
                    required
                    :disabled="isSubmitting"
                    class="mb-4"
                />
                <v-text-field
                    v-model="username"
                    prepend-inner-icon="mdi-email-outline"
                    :label="$t('auth.email')"
                    type="email"
                    :rules="[rules.validEmail, rules.requiredFor(t('auth.email'))]"
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
                    :rules="[rules.requiredFor(t('auth.password'))]"
                    variant="outlined"
                    density="comfortable"
                    :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                    @click:append-inner="showPassword = !showPassword"
                    required
                    :disabled="isSubmitting"
                    class="mb-4"
                />
                <v-text-field
                    v-model="confirmPassword"
                    prepend-inner-icon="mdi-repeat-variant"
                    :label="$t('auth.confirmPassword')"
                    :type="showPassword ? 'text' : 'password'"
                    :rules="[rules.requiredFor(t('auth.confirmPassword'))]"
                    variant="outlined"
                    density="comfortable"
                    required
                    :disabled="isSubmitting"
                    class="mb-4"
                />
                <v-btn
                    type="submit"
                    color="primary"
                    variant="elevated"
                    block
                    class="mt-2"
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
