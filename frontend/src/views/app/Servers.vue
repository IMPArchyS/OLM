<script setup lang="ts">
import { ref } from 'vue';
import ServerBrowser from '@/components/ServerBrowser.vue';
import DeviceBrowser from '@/components/DeviceBrowser.vue';
import type { Server } from '@/types/api';

const selectedServer = ref<Server | null>(null);

const handleSelectServer = (server: Server) => {
    selectedServer.value = server;
};

const handleServersLoaded = (servers: Server[]) => {
    if (!selectedServer.value && servers.length > 0 && servers[0]) {
        selectedServer.value = servers[0];
    }
};
</script>

<template>
    <ServerBrowser @select-server="handleSelectServer" @servers-loaded="handleServersLoaded" />
    <DeviceBrowser :selected-server="selectedServer" />
</template>
