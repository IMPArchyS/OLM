<script lang="ts" setup>
import DeviceBrowser from '@/components/servers/DeviceBrowser.vue';
import { useServers } from '@/composables/useServers';
import router from '@/router';
import { useToastStore } from '@/stores/toast';
import type { Server } from '@/types/api';
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';

const { t } = useI18n();
const toast = useToastStore();

const currentServer = ref<Server>({
    id: 0,
    name: '',
    ip_address: '',
    api_domain: '',
    port: 0,
});
const { getServerById, syncServer, restoreServer } = useServers();
const { params } = useRoute();

const serverId = +(params.id as string);
const loading = ref(false);
const showDeletedDevices = ref(false);

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

const handleRestore = async () => {
    const result = await restoreServer(currentServer.value.id);
    if (result.success) {
        toast.success(result.message || 'Success');
        await router.push({ name: 'servers' });
    } else {
        toast.error(result.message || 'Failed');
    }
};

const handleSync = async (item: Server) => {
    const result = await syncServer(item.id);

    if (result === null) {
        toast.error('Fatal error');
        return;
    }

    if (result.available) {
        toast.success('Server synced');
    } else {
        toast.warning('Server unreachable');
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

            <v-divider />

            <v-card-text v-if="!loading">
                <v-row class="mb-2">
                    <v-col cols="12" sm="6" md="3">
                        <div class="text-subtitle-2 text-medium-emphasis mb-1">{{ t('servers.name') }}</div>
                        <div class="text-body-1">{{ currentServer.name }}</div>
                    </v-col>
                    <v-col cols="12" sm="6" md="3">
                        <div class="text-subtitle-2 text-medium-emphasis mb-1">{{ t('servers.ipAddress') }}</div>
                        <div class="text-body-1">{{ currentServer.ip_address }}</div>
                    </v-col>
                    <v-col cols="12" sm="6" md="3">
                        <div class="text-subtitle-2 text-medium-emphasis mb-1">{{ t('servers.apiDomain') }}</div>
                        <div class="text-body-1">{{ currentServer.api_domain }}</div>
                    </v-col>
                    <v-col cols="12" sm="6" md="3">
                        <div class="text-subtitle-2 text-medium-emphasis mb-1">{{ t('servers.port') }}</div>
                        <div class="text-body-1">{{ currentServer.port }}</div>
                    </v-col>
                </v-row>

                <div class="d-flex flex-wrap ga-6">
                    <div>
                        <div class="text-subtitle-2 text-medium-emphasis mb-1">{{ t('servers.production') }}</div>
                        <v-chip :color="currentServer.production ? 'success' : 'default'" variant="tonal" size="small">
                            {{ currentServer.production ? t('common.yes') : t('common.no') }}
                        </v-chip>
                    </div>
                    <div>
                        <div class="text-subtitle-2 text-medium-emphasis mb-1">{{ t('servers.enabled') }}</div>
                        <v-chip :color="currentServer.enabled ? 'success' : 'default'" variant="tonal" size="small">
                            {{ currentServer.enabled ? t('common.yes') : t('common.no') }}
                        </v-chip>
                    </div>
                </div>
            </v-card-text>

            <v-card-actions v-if="!loading">
                <v-spacer />
                <v-btn prepend-icon="mdi-close" color="grey" variant="outlined" @click="handleBack">
                    {{ t('actions.back') }}
                </v-btn>
                <v-btn v-if="!currentServer.deleted_at" prepend-icon="mdi-sync" color="green" variant="elevated" @click="handleSync(currentServer)">
                    {{ t('actions.sync') }}
                </v-btn>
                <v-btn v-if="!currentServer.deleted_at" prepend-icon="mdi-pencil" color="primary" variant="elevated" @click="handleEdit">
                    {{ t('actions.edit') }}
                </v-btn>
                <v-btn v-if="currentServer.deleted_at" prepend-icon="mdi-restore" color="secondary" variant="elevated" @click="handleRestore">
                    {{ t('actions.restore') }}
                </v-btn>
            </v-card-actions>

            <v-divider />
            <div class="d-flex align-center px-4 py-2">
                <v-icon icon="mdi-devices" size="small" class="mr-2 text-medium-emphasis" />
                <span class="text-subtitle-1 font-weight-bold text-medium-emphasis">
                    {{ t('servers.devices') + ': ' + currentServer.name }}
                </span>
                <v-spacer />
                <v-switch
                    v-model="showDeletedDevices"
                    :label="t('devices.showDeleted')"
                    color="info"
                    hide-details
                    density="compact"
                />
            </div>
            <v-divider />
            <DeviceBrowser :selected-server="currentServer" :show-deleted="showDeletedDevices" />
        </v-card>
    </v-container>
</template>
