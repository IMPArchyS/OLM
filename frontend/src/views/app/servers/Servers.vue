<script setup lang="ts">
import { ref } from 'vue';
import DeviceBrowser from '@/views/app/servers/components/DeviceBrowser.vue';
import ServerBrowser from '@/views/app/servers/components/ServerBrowser.vue';
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
    <ServerBrowser @select-server="handleSelectServer" @servers-loaded="handleServersLoaded" />
    <DeviceBrowser :selected-server="selectedServer" />
</template>
