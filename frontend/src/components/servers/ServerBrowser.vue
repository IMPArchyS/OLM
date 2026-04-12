<script setup lang="ts">
import { useServers } from '@/composables/useServers';
import { onMounted, ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Server } from '@/types/api';
import router from '@/router';
import { useToastStore } from '@/stores/toast';

const { t } = useI18n();
const { servers, loading, error, fetchServers, getServer, syncServer, syncAllServers, softDeleteServer } = useServers();
const toast = useToastStore();

const emit = defineEmits<{
    selectServer: [server: Server];
    serversLoaded: [servers: Server[]];
}>();

const selectedDeviceServer = ref<Server | null>(null);
const showDeletedServers = ref(false);

const filteredServers = computed(() => {
    if (showDeletedServers.value) {
        return servers.value;
    } else {
        return servers.value.filter((server) => !server.deleted_at);
    }
});

onMounted(async () => {
    await fetchServers();
    if (servers.value.length > 0) {
        emit('serversLoaded', servers.value);
        const firstServer = servers.value.filter((server) => !server.deleted_at)[0];
        if (firstServer) {
            selectedDeviceServer.value = firstServer;
        }
    }
});

const handleCreate = () => {
    router.push('/app/servers/create');
};

const handleDevices = (item: Server) => {
    selectedDeviceServer.value = item;
    emit('selectServer', item);
};

const handleEdit = (item: Server) => {
    router.push(`/app/servers/${item.id}/edit`);
};

const handleDelete = async (item: Server) => {
    await softDeleteServer(item);
};

const handleView = (item: Server) => {
    router.push(`/app/servers/${item.id}/show`);
};

const syncedAvailability = ref<Record<number, boolean>>({});

const handleSync = async (item: Server) => {
    const result = await syncServer(item.id);

    if (result === null) {
        toast.error('Fatal error');
        return;
    }

    syncedAvailability.value[result.id] = result.available;

    if (result.available) {
        toast.success('Server synced');
    } else {
        toast.warning('Server unreachable');
    }
};

const handleSyncAll = async () => {
    const results = await syncAllServers();

    if (results === null) {
        toast.error('Fatal error');
        return;
    }

    results.forEach((result) => {
        syncedAvailability.value[result.id] = result.available;
    });

    const availableCount = results.filter((r) => r.available).length;
    const unavailableCount = results.filter((r) => !r.available).length;
    const errorCount = results.filter((r) => r.error).length;

    if (errorCount > 0) {
        toast.warning(`Synced ${results.length} servers: ${availableCount} available, ${unavailableCount} unavailable, ${errorCount} errors`);
    } else if (availableCount === results.length) {
        toast.success(`All ${results.length} servers are available`);
    } else if (unavailableCount === results.length) {
        toast.warning(`All ${results.length} servers are unavailable`);
    } else {
        toast.success(`Synced ${results.length} servers: ${availableCount} available, ${unavailableCount} unavailable`);
    }
};
</script>

<template>
    <v-container fluid>
        <v-data-table
            :headers="[
                {
                    title: t('servers.id'),
                    key: 'id',
                    sortable: true,
                },
                {
                    title: t('servers.name'),
                    key: 'name',
                    sortable: true,
                },
                {
                    title: t('servers.ipAddress'),
                    key: 'ip_address',
                    sortable: true,
                },
                {
                    title: t('servers.apiDomain'),
                    key: 'api_domain',
                    sortable: true,
                },
                {
                    title: t('servers.available'),
                    key: 'available',
                },
                {
                    title: t('servers.production'),
                    key: 'production',
                },
                {
                    title: t('servers.enabled'),
                    key: 'enabled',
                },
                {
                    title: t('servers.actions'),
                    key: 'actions',
                    sortable: false,
                    align: 'center' as const,
                },
            ]"
            :items="filteredServers"
            :loading="loading"
            :loading-text="t('servers.loadingServers')"
            class="elevation-1"
            item-value="id"
        >
            <template #top>
                <v-toolbar flat density="comfortable" class="px-2">
                    <v-toolbar-title class="text-h6">
                        {{ t('servers.servers') }}
                    </v-toolbar-title>
                    <v-spacer />
                    <div class="d-flex align-center flex-wrap justify-end ga-3">
                        <v-switch v-model="showDeletedServers" :label="t('servers.showDeleted')" color="info" hide-details />
                        <div class="d-flex align-center ga-2">
                            <v-btn color="success" variant="flat" prepend-icon="mdi-sync" @click="handleSyncAll">
                                {{ t('servers.syncServers') }}
                            </v-btn>
                            <v-btn color="primary" variant="flat" prepend-icon="mdi-plus" @click="handleCreate">
                                {{ t('servers.addServer') }}
                            </v-btn>
                        </div>
                    </div>
                </v-toolbar>
                <v-divider />
            </template>
            <!-- Available Column -->
            <template v-slot:item.available="{ item }">
                <v-icon
                    :color="(syncedAvailability[item.id] ?? item.available) ? 'success' : 'error'"
                    :icon="(syncedAvailability[item.id] ?? item.available) ? 'mdi-check-circle' : 'mdi-close-circle'"
                ></v-icon>
            </template>

            <!-- Production Column -->
            <template v-slot:item.production="{ item }">
                <v-icon :color="item.production ? 'success' : 'error'" :icon="item.production ? 'mdi-check-circle' : 'mdi-close-circle'"></v-icon>
            </template>

            <!-- Enabled Column -->
            <template v-slot:item.enabled="{ item }">
                <v-icon :color="item.enabled ? 'success' : 'error'" :icon="item.enabled ? 'mdi-check-circle' : 'mdi-close-circle'"></v-icon>
            </template>

            <!-- Actions Column -->
            <template v-slot:item.actions="{ item }">
                <v-btn
                    icon="mdi-toolbox"
                    size="small"
                    variant="text"
                    :color="selectedDeviceServer?.id === item.id ? '' : 'primary'"
                    @click="handleDevices(item)"
                ></v-btn>
                <v-btn icon="mdi-eye" size="small" variant="text" color="warning" @click="handleView(item)"></v-btn>
                <v-btn icon="mdi-sync" size="small" variant="text" color="success" @click="handleSync(item)"></v-btn>
                <v-btn icon="mdi-pencil" size="small" variant="text" color="primary" @click="handleEdit(item)"></v-btn>
                <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="handleDelete(item)"></v-btn>
            </template>

            <!-- No Data -->
            <template v-slot:no-data>
                <v-alert type="info" variant="tonal" class="ma-4">
                    {{ t('servers.noServersFound') }}
                </v-alert>
            </template>
        </v-data-table>

        <!-- Error Alert -->
        <v-alert v-if="error" type="error" variant="tonal" class="mt-4" closable>
            {{ error }}
        </v-alert>
    </v-container>
</template>
