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
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ t('actions.update') }}</span>
        </v-card-title>
        <v-card-text class="mt-5">
            <v-form @submit.prevent="handleProfileUpdate">
                <v-text-field
                    v-model="username"
                    :label="t('auth.username')"
                    type="text"
                    class="mb-4"
                    variant="outlined"
                    density="comfortable"
                ></v-text-field>
                <div class="d-flex justify-center">
                    <v-btn color="primary" class="w-3" type="submit" :disabled="isSubmitting">{{ t('actions.save') }}</v-btn>
                </div>
            </v-form>
        </v-card-text>
    </v-card>
</template>
