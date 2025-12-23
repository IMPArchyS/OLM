<script setup lang="ts">
import { useUserStore } from '@/stores/user';
import { useRouter } from 'vue-router';
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const userStore = useUserStore();
const router = useRouter();
const isOpen = ref(false);

const handleUpdateProfile = () => {
    userStore.updateProfile();
    isOpen.value = false;
    router.push({ name: 'update-profile' });
};

const handleUpdatePassword = () => {
    userStore.updatePassword();
    isOpen.value = false;
    router.push({ name: 'update-password' });
};

const handleLogout = () => {
    userStore.logout();
    isOpen.value = false;
    router.push({ name: 'login' });
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
        <!-- Logged In: User Dropdown -->
        <v-menu v-if="userStore.isLoggedIn" v-model="isOpen" :close-on-content-click="false">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props" variant="text" style="margin-right: 20px">
                    <span style="font-weight: 500">{{ userStore.user?.username }}</span>
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
                        <v-icon>mdi-account</v-icon>
                    </template>
                    <v-list-item-title>{{ t('profile.updateProfile') }}</v-list-item-title>
                </v-list-item>

                <v-list-item @click="handleUpdatePassword">
                    <template v-slot:prepend>
                        <v-icon>mdi-key</v-icon>
                    </template>
                    <v-list-item-title>{{ t('profile.updatePassword') }}</v-list-item-title>
                </v-list-item>

                <v-divider />

                <v-list-item @click="handleLogout" class="text-error">
                    <template v-slot:prepend>
                        <v-icon color="error">mdi-logout</v-icon>
                    </template>
                    <v-list-item-title style="color: rgb(var(--v-theme-error))">
                        {{ t('profile.logOut') }}
                    </v-list-item-title>
                </v-list-item>
            </v-list>
        </v-menu>

        <!-- Logged Out: Login & Register Links -->
        <div v-else style="display: flex; align-items: center; gap: 16px; margin-right: 24px">
            <v-btn @click="handleLogin" variant="text">
                {{ t('auth.login') }}
            </v-btn>
            <v-btn @click="handleRegister" variant="text">
                {{ t('auth.register') }}
            </v-btn>
        </div>
    </div>
</template>
