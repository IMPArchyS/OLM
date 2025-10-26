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
    <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
            <h2 class="card-title text-2xl mb-4">Register</h2>
            <form @submit.prevent="handleRegister">
                <div class="form-control mb-4">
                    <label class="label">
                        <span class="label-text">Username</span>
                    </label>
                    <input
                        v-model="username"
                        type="text"
                        placeholder="Choose a username"
                        class="input input-bordered w-full"
                        required
                    />
                </div>
                <div class="form-control mb-4">
                    <label class="label">
                        <span class="label-text">Email</span>
                    </label>
                    <input
                        v-model="email"
                        type="email"
                        placeholder="Enter your email"
                        class="input input-bordered w-full"
                        required
                    />
                </div>
                <div class="form-control mb-4">
                    <label class="label">
                        <span class="label-text">Password</span>
                    </label>
                    <input
                        v-model="password"
                        type="password"
                        placeholder="Choose a password"
                        class="input input-bordered w-full"
                        required
                    />
                </div>
                <div class="form-control mb-4">
                    <label class="label">
                        <span class="label-text">Confirm Password</span>
                    </label>
                    <input
                        v-model="confirmPassword"
                        type="password"
                        placeholder="Confirm your password"
                        class="input input-bordered w-full"
                        required
                    />
                </div>
                <div class="form-control mt-6">
                    <button type="submit" class="btn btn-primary w-full">Register</button>
                </div>
            </form>
            <div class="divider">OR</div>
            <router-link :to="{ name: 'login' }" class="btn btn-ghost w-full">
                Already have an account? Login
            </router-link>
        </div>
    </div>
</template>
