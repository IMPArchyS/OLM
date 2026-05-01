<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { useToastStore } from '@/stores/toast';
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const authStore = useAuthStore();
const toast = useToastStore();

const oldPassword = ref('');
const newPassword = ref('');
const repeatPassword = ref('');
const isSubmitting = ref(false);

const passwordErrors = computed(() => {
    const errors: string[] = [];

    if (newPassword.value && newPassword.value === oldPassword.value) {
        errors.push(t('auth.newPasswordSameAsOld'));
    }

    if (newPassword.value && repeatPassword.value && newPassword.value !== repeatPassword.value) {
        errors.push(t('auth.passwordsDoNotMatch'));
    }

    return errors;
});

const isFormValid = computed(() => {
    return Boolean(oldPassword.value) && Boolean(newPassword.value) && Boolean(repeatPassword.value) && passwordErrors.value.length === 0;
});

const handlePasswordUpdate = async () => {
    if (!isFormValid.value || isSubmitting.value) return;

    isSubmitting.value = true;

    const result = await authStore.updatePassword({
        password_old: oldPassword.value,
        password_new: newPassword.value,
        password_new_repeat: repeatPassword.value,
    });

    if (!result.success) {
        toast.error(result.message || t('auth.updatePasswordFailed'));
    } else {
        toast.success(t('auth.updatePasswordSuccess'));
        oldPassword.value = '';
        newPassword.value = '';
        repeatPassword.value = '';
    }

    isSubmitting.value = false;
};
</script>

<template>
    <v-card>
        <v-card-title class="bg-card-title">
            <v-icon icon="mdi-lock-reset" class="mr-2" />
            <span>{{ t('auth.updatePassword') }}</span>
        </v-card-title>
        <v-card-text class="mt-5">
            <v-form @submit.prevent="handlePasswordUpdate">
                <v-text-field
                    v-model="oldPassword"
                    :label="t('auth.oldPassword')"
                    type="password"
                    class="mb-4"
                    variant="outlined"
                    density="comfortable"
                    required
                ></v-text-field>
                <v-text-field
                    v-model="newPassword"
                    :label="t('auth.newPassword')"
                    type="password"
                    class="mb-4"
                    variant="outlined"
                    density="comfortable"
                    required
                ></v-text-field>
                <v-text-field
                    v-model="repeatPassword"
                    :label="t('auth.repeatPassword')"
                    type="password"
                    class="mb-2"
                    variant="outlined"
                    density="comfortable"
                    required
                ></v-text-field>

                <v-alert v-if="passwordErrors.length > 0" type="error" variant="tonal" class="mb-6">
                    <ul class="mb-0 pl-4">
                        <li v-for="error in passwordErrors" :key="error">{{ error }}</li>
                    </ul>
                </v-alert>
            </v-form>
        </v-card-text>
        <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn prepend-icon="mdi-plus" color="primary" variant="elevated" :disabled="isSubmitting || !isFormValid" @click="handlePasswordUpdate">
                {{ t('actions.save') }}
            </v-btn>
        </v-card-actions>
    </v-card>
</template>
