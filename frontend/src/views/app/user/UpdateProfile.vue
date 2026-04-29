<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { useToastStore } from '@/stores/toast';
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
const authStore = useAuthStore();
const toast = useToastStore();

const username = ref('');
const isSubmitting = ref(false);

const handleProfileUpdate = async () => {
    if (isSubmitting.value) return;

    isSubmitting.value = true;

    const result = await authStore.updateProfile({ jwt_token: localStorage.getItem('OLMAccessToken'), name: username.value });
    if (!result.success) {
        toast.error(result.message || 'Failed');
    } else {
        username.value = authStore.user?.name || username.value;
        toast.success(t('auth.updateNameSuccess'));
    }
    isSubmitting.value = false;
};

onMounted(() => {
    username.value = authStore.user?.name || '';
});
</script>
<template>
    <v-card>
        <v-card-title class="bg-card-title">
            <v-icon icon="mdi-account-edit" class="mr-2" />
            <span>{{ t('actions.update') }}</span>
        </v-card-title>
        <v-card-text class="mt-5">
            <v-form @submit.prevent="handleProfileUpdate">
                <v-text-field
                    v-model="username"
                    :label="t('auth.name')"
                    type="text"
                    class="mb-4"
                    variant="outlined"
                    density="comfortable"
                ></v-text-field>
            </v-form>
        </v-card-text>
        <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn prepend-icon="mdi-plus" color="primary" variant="elevated" :disabled="isSubmitting" @click="handleProfileUpdate">{{
                t('actions.save')
            }}</v-btn>
        </v-card-actions>
    </v-card>
</template>
