<script setup lang="ts">
import { ref } from 'vue';
import DeviceBrowser from '@/components/servers/DeviceBrowser.vue';
import ServerBrowser from '@/components/servers/ServerBrowser.vue';
import type { Server } from '@/types/api';

const selectedServer = ref<Server | null>(null);

const handleSelectServer = (server: Server) => {
    selectedServer.value = server;
};

const handleServersLoaded = (servers: Server[]) => {
    const filteredFirst = servers.filter((server) => !server.deleted_at)[0];
    if (!selectedServer.value && servers.length > 0 && filteredFirst) {
        selectedServer.value = filteredFirst;
    }
};
</script>

<template>
    <v-card>
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ $t('servers.title') }}</span>
        </v-card-title>
        <ServerBrowser @select-server="handleSelectServer" @servers-loaded="handleServersLoaded" />
        <v-divider />
        <DeviceBrowser :selected-server="selectedServer" />
    </v-card>
</template>
