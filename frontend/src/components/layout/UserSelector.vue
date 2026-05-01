<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const authStore = useAuthStore();
const router = useRouter();
const isOpen = ref(false);

const handleUpdateProfile = () => {
    isOpen.value = false;
    router.push({ name: 'update-profile' });
};

const handleUpdatePassword = () => {
    isOpen.value = false;
    router.push({ name: 'update-password' });
};

const handleLogout = async () => {
    isOpen.value = false;
    await authStore.logout();
};

const handleLogin = () => {
    router.push({ name: 'login' });
};

const handleRegister = () => {
    router.push({ name: 'register' });
};
</script>

<template>
    <div>
        <v-menu v-if="authStore.accessToken" v-model="isOpen" :close-on-content-click="false">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props" variant="text" class="mr-5">
                    <span class="font-weight-medium">{{ authStore.user?.name }}</span>
                    <v-icon
                        :style="{
                            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                            transition: 'transform 0.2s',
                        }"
                    >
                        mdi-chevron-down
                    </v-icon>
                </v-btn>
            </template>

            <v-list>
                <v-list-item @click="handleUpdateProfile">
                    <template v-slot:prepend>
                        <v-icon>mdi-account-edit</v-icon>
                    </template>
                    <v-list-item-title>{{ t('auth.updateProfile') }}</v-list-item-title>
                </v-list-item>

                <v-list-item @click="handleUpdatePassword">
                    <template v-slot:prepend>
                        <v-icon>mdi-lock-reset</v-icon>
                    </template>
                    <v-list-item-title>{{ t('auth.updatePassword') }}</v-list-item-title>
                </v-list-item>

                <v-divider />

                <v-list-item @click="handleLogout" class="text-error">
                    <template v-slot:prepend>
                        <v-icon color="error">mdi-logout</v-icon>
                    </template>
                    <v-list-item-title class="text-error">
                        {{ t('auth.logOut') }}
                    </v-list-item-title>
                </v-list-item>
            </v-list>
        </v-menu>

        <div v-else class="d-flex align-center ga-4 mr-6">
            <v-btn @click="handleLogin" variant="text">
                {{ t('auth.login') }}
            </v-btn>
            <v-btn @click="handleRegister" variant="text">
                {{ t('auth.register') }}
            </v-btn>
        </div>
    </div>
</template>
