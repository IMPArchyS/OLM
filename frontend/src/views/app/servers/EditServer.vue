<script lang="ts" setup>
import { useServers } from '@/composables/useServers';
import router from '@/router';
import { useToastStore } from '@/stores/toast';
import type { EditServerForm } from '@/types/forms';
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';

const { t } = useI18n();
const toast = useToastStore();

const formData = ref<EditServerForm>({});
const { nameRules, ipRules, domainRules, portRules, getServerById, updateServer } = useServers();
const { params } = useRoute();

const serverId = +(params.id as string);
const loading = ref(true);

onMounted(async () => {
    try {
        loading.value = true;
        const currentServer = await getServerById(serverId);

        if (currentServer) {
            formData.value = currentServer;
        } else {
            toast.info(t('servers.notFound'));
            router.back();
        }
    } catch (e) {
        toast.error(t('common.errorLoadingData'));
        router.back();
    } finally {
        loading.value = false;
    }
});

const valid = ref(false);

const handleSave = async () => {
    if (valid.value) {
        const result = await updateServer(formData.value);
        if (result.success) {
            toast.success(result.message || t('common.success'));
            await router.push({ name: 'servers' });
        } else {
            toast.error(result.message || t('common.error'));
        }
    } else {
        toast.error(t('validation.formInvalid'));
    }
};

const handleCancel = () => {
    router.push({ name: 'servers' });
    formData.value = {};
};
</script>
<template>
    <v-card :loading="loading" elevation="4">
        <v-card-title class="bg-card-title">
            <v-icon icon="mdi-pencil-box-outline" class="mr-2" />
            <span>{{ t('actions.edit') }}</span>
        </v-card-title>

        <v-divider></v-divider>

        <v-card-text v-if="!loading">
            <v-form v-model="valid">
                <v-text-field
                    v-model="formData.name"
                    :label="t('common.name')"
                    :rules="nameRules"
                    variant="outlined"
                    density="comfortable"
                    required
                ></v-text-field>

                <v-text-field
                    v-model="formData.ip_address"
                    :label="t('servers.ipAddress')"
                    :rules="ipRules"
                    variant="outlined"
                    density="comfortable"
                    required
                ></v-text-field>

                <v-text-field
                    v-model="formData.api_domain"
                    :label="t('servers.apiDomain')"
                    :rules="domainRules"
                    variant="outlined"
                    density="comfortable"
                    required
                ></v-text-field>

                <v-number-input
                    :model-value="formData.port"
                    label="Port"
                    :rules="portRules"
                    :step="1"
                    :min="1"
                    :max="65535"
                    variant="outlined"
                    density="comfortable"
                    required
                    @update:model-value="(v) => (formData.port = v ?? 0)"
                />

                <v-switch v-model="formData.production" :label="t('servers.production')" color="primary" hide-details></v-switch>
                <v-switch v-model="formData.enabled" :label="t('servers.enabled')" color="primary" hide-details></v-switch>
            </v-form>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn prepend-icon="mdi-close" color="grey" variant="outlined" @click="handleCancel">
                    {{ t('actions.cancel') }}
                </v-btn>
                <v-btn prepend-icon="mdi-plus" color="primary" variant="elevated" @click="handleSave">
                    {{ t('actions.save') }}
                </v-btn>
            </v-card-actions>
        </v-card-text>
    </v-card>
</template>
