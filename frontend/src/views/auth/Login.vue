<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const password = ref('')

const handleLogin = () => {
    // TODO: Implement your login logic
    console.log('Login attempt:', username.value)

    // After successful login, redirect to dashboard
    router.push({ name: 'dashboard' })
}
</script>

<template>
    <v-card max-width="400" class="mx-auto mt-5">
        <v-card-title class="text-h5 mb-4">Login</v-card-title>
        <v-card-text>
            <v-form @submit.prevent="handleLogin">
                <v-text-field
                    v-model="username"
                    label="Username"
                    placeholder="Enter username"
                    variant="outlined"
                    density="comfortable"
                    required
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
                    class="mb-4"
                />
                <v-btn type="submit" color="primary" variant="elevated" block class="mt-2">
                    Login
                </v-btn>
            </v-form>
            <v-divider class="my-4" />
            <v-btn :to="{ name: 'register' }" variant="text" block> Create an account </v-btn>
        </v-card-text>
    </v-card>
</template>
