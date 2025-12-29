<script lang="ts" setup>
import { useServers } from '@/composables/useServers';
import { useToast } from '@/composables/useToast';
import router from '@/router';
import type { EditServerForm } from '@/types/forms';
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';

const { t } = useI18n();
const { showSuccess, showError, showInfo } = useToast();

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
            showInfo(t('servers.notFound'));
            router.back();
        }
    } catch (e) {
        showError(t('common.errorLoadingData'));
        router.back();
    } finally {
        loading.value = false;
    }
});

// Form validation
const valid = ref(false);

const handleSave = async () => {
    if (valid.value) {
        const result = await updateServer(formData.value);
        if (result.success) {
            showSuccess(result.message || 'Success');
            await router.push({ name: 'servers' });
        } else {
            showError(result.message || 'Failed');
        }
    } else {
        showError(t('validation.formInvalid'));
    }
};

const handleCancel = () => {
    router.push({ name: 'servers' });
    formData.value = {};
};
</script>
<template>
    <v-container fluid>
        <v-card :loading="loading">
            <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
                <span class="text-h5">{{ t('servers.editServer') }}</span>
            </v-card-title>

            <v-divider></v-divider>

            <v-card-text v-if="!loading">
                <v-form v-model="valid">
                    <!-- Name -->
                    <v-text-field
                        v-model="formData.name"
                        :label="t('servers.name')"
                        :rules="nameRules"
                        variant="outlined"
                        density="comfortable"
                        required
                    ></v-text-field>

                    <!-- IP Address -->
                    <v-text-field
                        v-model="formData.ip_address"
                        :label="t('servers.ipAddress')"
                        :rules="ipRules"
                        variant="outlined"
                        density="comfortable"
                        required
                    ></v-text-field>

                    <!-- API Domain -->
                    <v-text-field
                        v-model="formData.api_domain"
                        :label="t('servers.apiDomain')"
                        :rules="domainRules"
                        variant="outlined"
                        density="comfortable"
                        required
                    ></v-text-field>

                    <!-- WebSocket Port -->
                    <v-text-field
                        v-model.number="formData.websocket_port"
                        label="WebSocket Port"
                        :rules="portRules"
                        type="number"
                        variant="outlined"
                        density="comfortable"
                        required
                    ></v-text-field>

                    <v-switch v-model="formData.production" :label="t('servers.production')" color="success" hide-details></v-switch>
                    <v-switch v-model="formData.enabled" :label="t('servers.enabled')" color="success" hide-details></v-switch>
                </v-form>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="grey" variant="text" @click="handleCancel">
                        {{ t('reservations.cancel') }}
                    </v-btn>
                    <v-btn color="primary" variant="elevated" @click="handleSave">
                        {{ t('reservations.save') }}
                    </v-btn>
                </v-card-actions>
            </v-card-text>
        </v-card>
    </v-container>
</template>
