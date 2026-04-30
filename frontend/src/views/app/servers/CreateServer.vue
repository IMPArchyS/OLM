<script lang="ts" setup>
import router from '@/router';
import type { CreateServerForm } from '@/types/forms';
import { useServers } from '@/composables/useServers';
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useToastStore } from '@/stores/toast';

const { t } = useI18n();
const { nameRules, ipRules, domainRules, portRules, createServer } = useServers();
const toast = useToastStore();

const formData = ref<CreateServerForm>({
    name: '',
    ip_address: '',
    api_domain: '',
    port: 0,
});

const valid = ref(false);

const handleCreate = async () => {
    if (valid.value) {
        const result = await createServer(formData.value);
        if (result.success) {
            toast.success(result.message || 'Success');
            await router.push({ name: 'servers' });
        } else {
            toast.error(result.message || 'Failed');
        }
    } else {
        toast.error(t('validation.formInvalid'));
    }
};

const handleCancel = () => {
    router.push({ name: 'servers' });
    formData.value = {
        name: '',
        ip_address: '',
        api_domain: '',
        port: 0,
    };
};
</script>

<template>
    <v-card elevation="4">
        <v-card-title class="bg-card-title">
            <v-icon icon="mdi-plus-box-outline" class="mr-2" />
            <span>{{ t('actions.create') }}</span>
        </v-card-title>

        <v-divider></v-divider>

        <v-card-text>
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

                <v-text-field
                    v-model="formData.port"
                    label="Port"
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
            <v-btn prepend-icon="mdi-close" color="grey" variant="outlined" @click="handleCancel">
                {{ t('actions.cancel') }}
            </v-btn>
            <v-btn prepend-icon="mdi-plus" color="primary" variant="elevated" @click="handleCreate">
                {{ t('actions.create') }}
            </v-btn>
        </v-card-actions>
    </v-card>
</template>
