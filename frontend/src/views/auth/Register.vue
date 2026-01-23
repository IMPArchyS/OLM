<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useUserStore } from '@/stores/user';

const router = useRouter();
const authStore = useAuthStore();
const userStore = useUserStore();

const username = ref('');
const name = ref('');
const password = ref('');
const confirmPassword = ref('');
const isSubmitting = ref(false);

const handleRegister = async () => {
    if (isSubmitting.value) return;

    // Validate passwords match
    if (password.value !== confirmPassword.value) {
        authStore.error = 'Passwords do not match';
        return;
    }

    isSubmitting.value = true;

    try {
        // Register and get tokens
        await authStore.register({
            name: name.value,
            username: username.value,
            password: password.value,
        });

        // Fetch user data
        await userStore.fetchUser(username.value);

        // Redirect to dashboard
        await router.push({ name: 'dashboard' });
    } catch (error) {
        console.error('Registration failed:', error);
    } finally {
        isSubmitting.value = false;
    }
};
</script>

<template>
    <v-card max-width="400" class="mx-auto mt-5">
        <v-card-title class="text-h5 mb-4">Register</v-card-title>
        <v-card-text>
            <v-alert v-if="authStore.error" type="error" class="mb-4" closable @click:close="authStore.clearError()">
                {{ authStore.error }}
            </v-alert>

            <v-form @submit.prevent="handleRegister">
                <v-text-field
                    v-model="name"
                    label="Name"
                    placeholder="Choose a name"
                    variant="outlined"
                    density="comfortable"
                    required
                    :disabled="isSubmitting"
                    class="mb-4"
                />
                <v-text-field
                    v-model="username"
                    label="Email"
                    placeholder="Enter your email"
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
                    placeholder="Choose a password"
                    type="password"
                    variant="outlined"
                    density="comfortable"
                    required
                    :disabled="isSubmitting"
                    class="mb-4"
                />
                <v-text-field
                    v-model="confirmPassword"
                    label="Confirm Password"
                    placeholder="Confirm your password"
                    type="password"
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
                    Register
                </v-btn>
            </v-form>
            <v-divider class="my-4" />
            <v-btn :to="{ name: 'login' }" variant="text" block> Already have an account? Login </v-btn>
        </v-card-text>
    </v-card>
</template>
