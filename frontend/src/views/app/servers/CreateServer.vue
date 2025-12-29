<script lang="ts" setup>
import router from '@/router';
import type { CreateServerForm } from '@/types/forms';
import { useServers } from '@/composables/useServers';
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useToast } from '@/composables/useToast';

const { t } = useI18n();
const { nameRules, ipRules, domainRules, portRules, createServer } = useServers();
const { showSuccess, showError } = useToast();

const formData = ref<CreateServerForm>({});

const valid = ref(false);

const handleCreate = async () => {
    if (valid.value) {
        const result = await createServer(formData.value);
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
        <v-card>
            <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
                <span class="text-h5">{{ t('servers.addServer') }}</span>
            </v-card-title>

            <v-divider></v-divider>

            <v-card-text>
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
                        v-model="formData.websocket_port"
                        label="WebSocket Port"
                        :rules="portRules"
                        type="number"
                        variant="outlined"
                        density="comfortable"
                        required
                    ></v-text-field>
                </v-form>
            </v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="grey" variant="text" @click="handleCancel">
                    {{ t('reservations.cancel') }}
                </v-btn>
                <v-btn color="primary" variant="elevated" @click="handleCreate">
                    {{ t('servers.addServer') }}
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-container>
</template>
