<script lang="ts" setup>
import DeviceBrowser from '@/views/app/servers/components/DeviceBrowser.vue';
import { useServers } from '@/composables/useServers';
import { useToast } from '@/composables/useToast';
import router from '@/router';
import type { Server } from '@/types/api';
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';

const { t } = useI18n();
const { showSuccess, showError, showWarning, showInfo } = useToast();

const currentServer = ref<Server>({
    id: 0,
    name: '',
    ip_address: '',
    api_domain: '',
    port: 0,
});
const { nameRules, ipRules, domainRules, portRules, getServerById, syncServer, restoreServer } = useServers();
const { params } = useRoute();

const serverId = +(params.id as string);
const loading = ref(false);

const handleEdit = () => {
    router.push(`/app/servers/${serverId}/edit`);
};

onMounted(async () => {
    try {
        loading.value = true;
        const fetchedServer = await getServerById(serverId);

        if (fetchedServer) {
            currentServer.value = fetchedServer;
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

const handleRestore = async () => {
    const result = await restoreServer(currentServer.value.id);
    if (result.success) {
        showSuccess(result.message || 'Success');
        await router.push({ name: 'servers' });
    } else {
        showError(result.message || 'Failed');
    }
};

const handleSync = async (item: Server) => {
    const result = await syncServer(item.id);

    if (result === null) {
        showError('Fatal error');
        return;
    }

    if (result.available) {
        showSuccess('Server synced');
    } else {
        showWarning('Server unreachable');
    }
};

const handleBack = () => {
    router.push({ name: 'servers' });
};
</script>
<template>
    <v-container fluid>
        <v-card :loading="loading">
            <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
                <span class="text-h5">{{ t('servers.viewServer') }}</span>
            </v-card-title>

            <v-divider></v-divider>

            <v-card-text v-if="!loading">
                <v-text-field
                    v-model="currentServer.name"
                    :label="t('servers.name')"
                    :rules="nameRules"
                    variant="outlined"
                    density="comfortable"
                    readonly
                ></v-text-field>

                <!-- IP Address -->
                <v-text-field
                    v-model="currentServer.ip_address"
                    :label="t('servers.ipAddress')"
                    :rules="ipRules"
                    variant="outlined"
                    density="comfortable"
                    readonly
                ></v-text-field>

                <!-- API Domain -->
                <v-text-field
                    v-model="currentServer.api_domain"
                    :label="t('servers.apiDomain')"
                    :rules="domainRules"
                    variant="outlined"
                    density="comfortable"
                    readonly
                ></v-text-field>

                <!-- Port -->
                <v-text-field
                    v-model.number="currentServer.port"
                    label="Port"
                    :rules="portRules"
                    type="number"
                    variant="outlined"
                    density="comfortable"
                    readonly
                ></v-text-field>

                <v-switch v-model="currentServer.production" :label="t('servers.production')" color="success" hide-details readonly></v-switch>
                <v-switch v-model="currentServer.enabled" :label="t('servers.enabled')" color="success" hide-details readonly></v-switch>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="grey" variant="text" @click="handleBack">
                        {{ t('actions.back') }}
                    </v-btn>
                    <v-btn v-if="!currentServer.deleted_at" color="green" variant="elevated" @click="handleSync(currentServer)">
                        {{ t('actions.sync') }}
                    </v-btn>
                    <v-btn v-if="!currentServer.deleted_at" color="primary" variant="elevated" @click="handleEdit">
                        {{ t('actions.edit') }}
                    </v-btn>
                    <v-btn v-if="currentServer.deleted_at" color="secondary" variant="elevated" @click="handleRestore">
                        {{ t('actions.restore') }}
                    </v-btn>
                </v-card-actions>
            </v-card-text>
        </v-card>
    </v-container>
    <DeviceBrowser :selected-server="currentServer" />
</template>
