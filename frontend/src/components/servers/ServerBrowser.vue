<script setup lang="ts">
import { useServers } from '@/composables/useServers';
import { onMounted, ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Server } from '@/types/api';
import router from '@/router';
import { useToastStore } from '@/stores/toast';

const { t } = useI18n();
const { servers, loading, fetchServers, syncServerWithToast, syncAllServers, softDeleteServer, restoreServer } = useServers();
const toast = useToastStore();

const props = defineProps<{
    showDeleted: boolean;
}>();

const emit = defineEmits<{
    selectServer: [server: Server];
    serversLoaded: [servers: Server[]];
}>();

const selectedDeviceServer = ref<Server | null>(null);

const filteredServers = computed(() => {
    if (props.showDeleted) {
        return servers.value;
    } else {
        return servers.value.filter((server) => !server.deleted_at);
    }
});

onMounted(async () => {
    const result = await fetchServers();
    if (!result.success) {
        toast.error(result.message || t('common.error'));
    }
    if (servers.value.length > 0) {
        emit('serversLoaded', servers.value);
        const firstServer = servers.value.filter((server) => !server.deleted_at)[0];
        if (firstServer) {
            selectedDeviceServer.value = firstServer;
        }
    }
});

const handleDevices = (item: Server) => {
    selectedDeviceServer.value = item;
    emit('selectServer', item);
};

const handleEdit = (item: Server) => {
    router.push(`/app/servers/${item.id}/edit`);
};

const handleDelete = async (item: Server) => {
    const result = await softDeleteServer(item);
    if (result.success) {
        toast.success(t('servers.deleted'));
    } else {
        toast.error(result.message || t('common.error'));
    }
};

const handleView = (item: Server) => {
    router.push(`/app/servers/${item.id}/show`);
};

const handleRestore = async (item: Server) => {
    const result = await restoreServer(item.id);
    if (result.success) {
        toast.success(t('servers.restored'));
    } else {
        toast.error(result.message || t('common.error'));
    }
};

const syncedAvailability = ref<Record<number, boolean>>({});

const handleSync = async (item: Server) => {
    const result = await syncServerWithToast(item.id);
    if (result !== null) {
        syncedAvailability.value[result.id] = result.available;
    }
};

const handleSyncAll = async () => {
    const results = await syncAllServers();

    if (results === null) {
        toast.error(t('common.error'));
        return;
    }

    results.forEach((result) => {
        syncedAvailability.value[result.id] = result.available;
    });

    const availableCount = results.filter((r) => r.available).length;
    const unavailableCount = results.filter((r) => !r.available).length;
    const errorCount = results.filter((r) => r.error).length;
    const total = results.length;

    if (errorCount > 0) {
        toast.warning(t('servers.syncAllErrors', { total, available: availableCount, unavailable: unavailableCount, errors: errorCount }));
    } else if (availableCount === total) {
        toast.success(t('servers.syncAllAvailable', { total }));
    } else if (unavailableCount === total) {
        toast.warning(t('servers.syncAllUnavailable', { total }));
    } else {
        toast.success(t('servers.syncAllResult', { total, available: availableCount, unavailable: unavailableCount }));
    }
};

const tableHeaders = [
    { title: t('common.id'), key: 'id', sortable: true },
    { title: t('common.name'), key: 'name', sortable: true },
    { title: t('servers.ipAddress'), key: 'ip_address', sortable: true },
    { title: t('servers.apiDomain'), key: 'api_domain', sortable: true },
    { title: t('servers.available'), key: 'available', sortable: false },
    { title: t('servers.production'), key: 'production', sortable: false },
    { title: t('servers.enabled'), key: 'enabled', sortable: false },
    { title: t('common.actions'), key: 'actions', sortable: false, align: 'center' as const },
];

defineExpose({ handleSyncAll });
</script>

<template>
    <v-data-table
        :headers="tableHeaders"
        :items="filteredServers"
        :loading="loading"
        :row-props="({ item }) => ({ class: item.deleted_at ? 'text-error' : '' })"
        item-value="id"
    >
        <template v-slot:item.available="{ item }">
            <v-icon
                :color="(syncedAvailability[item.id] ?? item.available) ? 'success' : 'error'"
                :icon="(syncedAvailability[item.id] ?? item.available) ? 'mdi-check-circle' : 'mdi-close-circle'"
            ></v-icon>
        </template>

        <template v-slot:item.production="{ item }">
            <v-icon :color="item.production ? 'success' : 'error'" :icon="item.production ? 'mdi-check-circle' : 'mdi-close-circle'"></v-icon>
        </template>

        <template v-slot:item.enabled="{ item }">
            <v-icon :color="item.enabled ? 'success' : 'error'" :icon="item.enabled ? 'mdi-check-circle' : 'mdi-close-circle'"></v-icon>
        </template>

        <template v-slot:item.actions="{ item }">
            <v-btn
                icon="mdi-toolbox"
                size="small"
                variant="text"
                :color="selectedDeviceServer?.id === item.id ? '' : 'primary'"
                @click="handleDevices(item)"
            ></v-btn>
            <v-btn icon="mdi-eye" size="small" variant="text" color="warning" @click="handleView(item)"></v-btn>
            <v-btn v-if="!item.deleted_at" icon="mdi-sync" size="small" variant="text" color="success" @click="handleSync(item)"></v-btn>
            <v-btn v-if="!item.deleted_at" icon="mdi-pencil" size="small" variant="text" color="primary" @click="handleEdit(item)"></v-btn>
            <v-btn v-if="!item.deleted_at" icon="mdi-trash-can" size="small" variant="text" color="error" @click="handleDelete(item)"></v-btn>
            <v-btn v-if="item.deleted_at" icon="mdi-restore" size="small" variant="text" color="secondary" @click="handleRestore(item)"></v-btn>
        </template>
    </v-data-table>
</template>
