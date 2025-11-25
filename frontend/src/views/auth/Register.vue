<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')

const handleRegister = () => {
    // TODO: Implement your registration logic
    if (password.value !== confirmPassword.value) {
        alert('Passwords do not match')
        return
    }

    console.log('Register attempt:', username.value, email.value)

    // After successful registration, redirect to login
    router.push({ name: 'login' })
}
</script>

<template>
    <v-card max-width="400" class="mx-auto mt-5">
        <v-card-title class="text-h5 mb-4">Register</v-card-title>
        <v-card-text>
            <v-form @submit.prevent="handleRegister">
                <v-text-field
                    v-model="username"
                    label="Username"
                    placeholder="Choose a username"
                    variant="outlined"
                    density="comfortable"
                    required
                    class="mb-4"
                />
                <v-text-field
                    v-model="email"
                    label="Email"
                    placeholder="Enter your email"
                    type="email"
                    variant="outlined"
                    density="comfortable"
                    required
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
                    class="mb-4"
                />
                <v-btn type="submit" color="primary" variant="elevated" block class="mt-2">
                    Register
                </v-btn>
            </v-form>
            <v-divider class="my-4" />
            <v-btn :to="{ name: 'login' }" variant="text" block>
                Already have an account? Login
            </v-btn>
        </v-card-text>
    </v-card>
</template>
