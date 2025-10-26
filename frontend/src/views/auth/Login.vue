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
    <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
            <h2 class="card-title text-2xl mb-4">Login</h2>
            <form @submit.prevent="handleLogin">
                <div class="form-control mb-4">
                    <label class="label">
                        <span class="label-text">Username</span>
                    </label>
                    <input
                        v-model="username"
                        type="text"
                        placeholder="Enter username"
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
                        placeholder="Enter password"
                        class="input input-bordered w-full"
                        required
                    />
                </div>
                <div class="form-control mt-6">
                    <button type="submit" class="btn btn-primary w-full">Login</button>
                </div>
            </form>
            <div class="divider">OR</div>
            <router-link :to="{ name: 'register' }" class="btn btn-ghost w-full">
                Create an account
            </router-link>
        </div>
    </div>
</template>
