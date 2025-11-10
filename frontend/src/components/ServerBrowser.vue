<script setup lang="ts">
import { useServers } from '@/composables/useServers'
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Server } from '@/types/api'

const { t } = useI18n()
const { servers, loading, error, fetchServers } = useServers()

const emit = defineEmits<{
    selectServer: [server: Server]
    serversLoaded: [servers: Server[]]
}>()

onMounted(async () => {
    await fetchServers()
    console.log(servers.value)
    if (servers.value.length > 0) {
        emit('serversLoaded', servers.value)
    }
})

const handleCreate = () => {
    console.log('Create new server')
    // TODO: Implement create logic
}

const handleDevices = (item: Server) => {
    console.log('Show devices for server:', item)
    emit('selectServer', item)
}

const handleEdit = (item: Server) => {
    console.log('Edit server:', item)
    // TODO: Implement edit logic
}

const handleDelete = (item: Server) => {
    console.log('Delete server:', item)
    // TODO: Implement delete logic
}

const handleView = (item: Server) => {
    console.log('View server:', item)
    // TODO: Implement view logic
}

const handleSync = (item: Server) => {
    console.log('Sync server:', item)
    // TODO: Implement sync logic
}

const handleSyncAll = async () => {
    console.log('Sync all servers')
    await fetchServers()
    // TODO: Implement sync all logic
}
</script>

<template>
    <v-container fluid>
        <v-card>
            <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
                <span class="text-h5">{{ t('servers.title') }}</span>
                <div class="d-flex gap-2">
                    <v-btn color="success" prepend-icon="mdi-sync" @click="handleSyncAll">
                        {{ t('servers.syncServers') }}
                    </v-btn>
                    <v-btn color="primary" prepend-icon="mdi-plus" @click="handleCreate">
                        {{ t('servers.addServer') }}
                    </v-btn>
                </div>
            </v-card-title>

            <v-divider></v-divider>

            <v-card-text>
                <v-data-table
                    :headers="[
                        { title: t('servers.id'), key: 'id', sortable: true },
                        { title: t('servers.name'), key: 'name', sortable: true },
                        { title: t('servers.ipAddress'), key: 'ip_address', sortable: true },
                        { title: t('servers.apiDomain'), key: 'api_domain', sortable: true },
                        {
                            title: t('servers.available'),
                            key: 'available',
                            align: 'center' as const,
                        },
                        {
                            title: t('servers.production'),
                            key: 'production',
                            align: 'center' as const,
                        },
                        { title: t('servers.enabled'), key: 'enabled', align: 'center' as const },
                        {
                            title: t('servers.actions'),
                            key: 'actions',
                            sortable: false,
                            align: 'center' as const,
                        },
                    ]"
                    :items="servers"
                    :loading="loading"
                    :loading-text="t('servers.loadingServers')"
                    class="elevation-1"
                    item-value="id"
                >
                    <!-- Available Column -->
                    <template v-slot:item.available="{ item }">
                        <v-icon
                            :color="item.available ? 'success' : 'error'"
                            :icon="item.available ? 'mdi-check-circle' : 'mdi-close-circle'"
                        ></v-icon>
                    </template>

                    <!-- Production Column -->
                    <template v-slot:item.production="{ item }">
                        <v-icon
                            :color="item.production ? 'success' : 'error'"
                            :icon="item.production ? 'mdi-check-circle' : 'mdi-close-circle'"
                        ></v-icon>
                    </template>

                    <!-- Enabled Column -->
                    <template v-slot:item.enabled="{ item }">
                        <v-icon
                            :color="item.enabled ? 'success' : 'error'"
                            :icon="item.enabled ? 'mdi-check-circle' : 'mdi-close-circle'"
                        ></v-icon>
                    </template>

                    <!-- Actions Column -->
                    <template v-slot:item.actions="{ item }">
                        <v-btn
                            icon="mdi-toolbox"
                            size="small"
                            variant="text"
                            @click="handleDevices(item)"
                        ></v-btn>
                        <v-btn
                            icon="mdi-eye"
                            size="small"
                            variant="text"
                            color="warning"
                            @click="handleView(item)"
                        ></v-btn>
                        <v-btn
                            icon="mdi-sync"
                            size="small"
                            variant="text"
                            color="success"
                            @click="handleSync(item)"
                        ></v-btn>
                        <v-btn
                            icon="mdi-pencil"
                            size="small"
                            variant="text"
                            color="primary"
                            @click="handleEdit(item)"
                        ></v-btn>
                        <v-btn
                            icon="mdi-delete"
                            size="small"
                            variant="text"
                            color="error"
                            @click="handleDelete(item)"
                        ></v-btn>
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
            </v-card-text>
        </v-card>
    </v-container>
</template>
