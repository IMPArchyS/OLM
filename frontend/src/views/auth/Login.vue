<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useUserStore } from '@/stores/user';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const userStore = useUserStore();

const username = ref('');
const password = ref('');
const isSubmitting = ref(false);

const handleLogin = async () => {
    if (isSubmitting.value) return;

    isSubmitting.value = true;

    try {
        // Login and get tokens
        await authStore.login({
            username: username.value,
            password: password.value,
        });

        // Fetch user data
        await userStore.fetchUser(username.value);

        // Redirect to intended page or dashboard
        const redirect = (route.query.redirect as string) || '/app/dashboard';
        await router.push(redirect);
    } catch (error) {
        console.error('Login failed:', error);
        // Error is already stored in authStore.error
    } finally {
        isSubmitting.value = false;
    }
};
</script>

<template>
    <v-card max-width="400" class="mx-auto mt-5">
        <v-card-title class="text-h5 mb-4">Login</v-card-title>
        <v-card-text>
            <v-alert v-if="authStore.error" type="error" class="mb-4" closable @click:close="authStore.clearError()">
                {{ authStore.error }}
            </v-alert>

            <v-form @submit.prevent="handleLogin">
                <v-text-field
                    v-model="username"
                    label="Username"
                    placeholder="Enter username"
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
