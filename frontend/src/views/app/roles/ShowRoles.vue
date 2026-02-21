<script lang="ts" setup>
import { useRoles } from '@/composables/useRoles';
import { useToast } from '@/composables/useToast';
import router from '@/router';
import type { Role } from '@/types/api';
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';

const { t } = useI18n();
const { params } = useRoute();
const { showSuccess, showError, showInfo } = useToast();
const { getRoleById } = useRoles();

const currentRole = ref<Role>({
    id: 0,
    name: '',
    description: '',
    permissions: [],
});

const roleId = +(params.id as string);
const loading = ref(false);

onMounted(async () => {
    try {
        loading.value = true;
        const fetchedRole = await getRoleById(roleId);

        if (fetchedRole) {
            currentRole.value = fetchedRole;
        } else {
            showInfo(t('roles.notFound'));
            router.back();
        }
    } catch (e) {
        showError(t('common.errorLoadingData'));
        router.back();
    } finally {
        loading.value = false;
    }
});

const handleBack = () => {
    router.push({ name: 'roles' });
};
</script>
<template>
    <v-card class="mt-5">
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5"> {{ currentRole.name }} </span>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
            <v-card-title class="px-0 text-h5"> </v-card-title>
            <v-list class="px-0" density="compact">
                <v-list-item v-for="perm in currentRole.permissions" :key="perm.name">
                    <v-chip class="text-subtitle-1" variant="outlined" color="primary">
                        {{ perm.name }}
                    </v-chip>
                    <v-list-item-subtitle class="m-2!">
                        {{ perm.description }}
                    </v-list-item-subtitle>
                </v-list-item>
            </v-list>
            <v-alert v-if="currentRole.permissions.length === 0" type="info" variant="tonal" class="ma-4">
                {{ t('roles.noRoles') }}
            </v-alert>
            <div class="d-flex justify-end mt-4">
                <v-btn color="grey" variant="text" @click="handleBack">
                    {{ t('actions.back') }}
                </v-btn>
            </div>
        </v-card-text>
    </v-card>
</template>
