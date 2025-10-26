<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { ref } from 'vue'

const userStore = useUserStore()
const router = useRouter()
const isOpen = ref(false)

const toggleDropdown = () => {
    isOpen.value = !isOpen.value
}

const closeDropdown = () => {
    isOpen.value = false
}

const handleUpdateProfile = () => {
    userStore.updateProfile()
    closeDropdown()
}

const handleUpdatePassword = () => {
    userStore.updatePassword()
    closeDropdown()
}

const handleLogout = () => {
    userStore.logout()
    closeDropdown()
}

const handleLogin = () => {
    router.push({ name: 'login' })
}

const handleRegister = () => {
    router.push({ name: 'register' })
}
</script>

<template>
    <div class="relative">
        <!-- Logged In: User Dropdown -->
        <div v-if="userStore.isLoggedIn" v-click-outside="closeDropdown">
            <button @click="toggleDropdown" class="btn btn-ghost gap-2 normal-case" type="button">
                <span class="font-medium">{{ userStore.user?.username }}</span>
                <svg
                    class="w-4 h-4 transition-transform duration-200"
                    :class="{ 'rotate-180': isOpen }"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 9l-7 7-7-7"
                    />
                </svg>
            </button>

            <!-- Dropdown Menu -->
            <transition
                enter-active-class="transition ease-out duration-200"
                enter-from-class="opacity-0 translate-y-1"
                enter-to-class="opacity-100 translate-y-0"
                leave-active-class="transition ease-in duration-150"
                leave-from-class="opacity-100 translate-y-0"
                leave-to-class="opacity-0 translate-y-1"
            >
                <div
                    v-if="isOpen"
                    class="absolute right-0 mt-2 w-56 rounded-lg shadow-lg bg-base-100 border border-base-300 z-50"
                >
                    <!-- Menu Items -->
                    <ul class="menu p-2">
                        <li>
                            <button @click="handleUpdateProfile" class="flex items-center gap-3">
                                <svg
                                    class="w-5 h-5"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                                    />
                                </svg>
                                <span>Update Profile</span>
                            </button>
                        </li>
                        <li>
                            <button @click="handleUpdatePassword" class="flex items-center gap-3">
                                <svg
                                    class="w-5 h-5"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
                                    />
                                </svg>
                                <span>Update Password</span>
                            </button>
                        </li>
                        <li class="border-t border-base-300 mt-1 pt-1">
                            <button
                                @click="handleLogout"
                                class="flex items-center gap-3 text-error hover:bg-error hover:text-error-content"
                            >
                                <svg
                                    class="w-5 h-5"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                                    />
                                </svg>
                                <span>Log Out</span>
                            </button>
                        </li>
                    </ul>
                </div>
            </transition>
        </div>

        <!-- Logged Out: Login & Register Links -->
        <div v-else class="flex items-center gap-4">
            <button @click="handleLogin" class="link link-hover font-medium">Login</button>
            <button @click="handleRegister" class="link link-hover link-primary font-medium">
                Register
            </button>
        </div>
    </div>
</template>

<style scoped>
.menu li button {
    padding: 0.75rem;
    transition: all 0.2s ease;
}

.menu li button:hover {
    background-color: hsl(var(--b3));
}
</style>
