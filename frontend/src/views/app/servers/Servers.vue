<script setup lang="ts">
import { ref } from 'vue';
import DeviceBrowser from '@/components/servers/DeviceBrowser.vue';
import ServerBrowser from '@/components/servers/ServerBrowser.vue';
import router from '@/router';
import type { Server } from '@/types/api';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const selectedServer = ref<Server | null>(null);
const showDeletedServers = ref(false);
const showDeletedDevices = ref(false);
const serverBrowserRef = ref<InstanceType<typeof ServerBrowser> | null>(null);

const handleSelectServer = (server: Server) => {
    selectedServer.value = server;
};

const handleServersLoaded = (servers: Server[]) => {
    const filteredFirst = servers.filter((server) => !server.deleted_at)[0];
    if (!selectedServer.value && servers.length > 0 && filteredFirst) {
        selectedServer.value = filteredFirst;
    }
};

const handleCreate = () => {
    router.push('/app/servers/create');
};

const handleSyncAll = () => {
    serverBrowserRef.value?.handleSyncAll();
};
</script>

<template>
    <v-card elevation="4">
        <v-card-title class="bg-card-title d-flex align-center flex-wrap ga-3">
            <v-icon icon="mdi-server" class="mr-2" />
            <span>{{ t('servers.title') }}</span>
            <v-spacer />
            <v-switch v-model="showDeletedServers" :label="t('servers.showDeleted')" color="primary" hide-details density="compact" />
            <v-btn color="success" variant="flat" prepend-icon="mdi-sync" @click="handleSyncAll">
                {{ t('servers.syncServers') }}
            </v-btn>
            <v-btn color="primary" variant="flat" prepend-icon="mdi-plus" @click="handleCreate">
                {{ t('servers.addServer') }}
            </v-btn>
        </v-card-title>
        <v-divider />
        <ServerBrowser
            ref="serverBrowserRef"
            :show-deleted="showDeletedServers"
            @select-server="handleSelectServer"
            @servers-loaded="handleServersLoaded"
        />
        <v-divider />
        <div class="d-flex align-center px-4 py-2">
            <v-icon icon="mdi-devices" size="small" class="mr-2 text-medium-emphasis" />
            <span class="text-subtitle-1 font-weight-bold text-medium-emphasis">
                {{ selectedServer ? t('servers.devices') + ': ' + selectedServer.name : t('devices.selectServer') }}
            </span>
            <v-spacer />
            <v-switch
                v-if="selectedServer"
                v-model="showDeletedDevices"
                :label="t('devices.showDeleted')"
                color="info"
                hide-details
                density="compact"
            />
        </div>
        <v-divider />
        <DeviceBrowser :selected-server="selectedServer" :show-deleted="showDeletedDevices" />
    </v-card>
</template>
