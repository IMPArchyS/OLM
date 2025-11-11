<script setup lang="ts">
import { useServers } from '@/composables/useServers'
import { onMounted, ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Server } from '@/types/api'
import ServerDetailsModal from './ServerDetailsModal.vue'
import ServerEditModal from './ServerEditModal.vue'
import ServerCreateModal from './ServerCreateModal.vue'

const { t } = useI18n()
const {
    servers,
    loading,
    error,
    fetchServers,
    updateServer,
    getServer,
    createServer,
    softDeleteServer,
} = useServers()

const emit = defineEmits<{
    selectServer: [server: Server]
    serversLoaded: [servers: Server[]]
}>()

const showDetailsModal = ref(false)
const showEditModal = ref(false)
const showCreateModal = ref(false)
const selectedServer = ref<Server | null>(null)
const showDeleted = ref(false)

// Computed property to filter servers based on deleted_at
const filteredServers = computed(() => {
    if (showDeleted.value) {
        // Show only deleted servers
        return servers.value.filter((server) => server.deleted_at)
    } else {
        // Show only non-deleted servers
        return servers.value.filter((server) => !server.deleted_at)
    }
})

onMounted(async () => {
    await fetchServers()
    if (servers.value.length > 0) {
        emit('serversLoaded', servers.value)
    }
})

const handleCreate = async () => {
    showCreateModal.value = true
}

const handleDevices = (item: Server) => {
    console.log('Show devices for server:', item)
    emit('selectServer', item)
}

const handleEdit = (item: Server) => {
    selectedServer.value = item
    showEditModal.value = true
}

const handleDelete = async (item: Server) => {
    console.log('Delete server:', item)
    await softDeleteServer(item)
}

const handleView = (item: Server) => {
    selectedServer.value = item
    showDetailsModal.value = true
}

const handleSync = async (item: Server) => {
    console.log('Sync server:', item)
    await getServer(item)
}

const handleEditFromDetails = (server: Server) => {
    selectedServer.value = server
    showEditModal.value = true
}

const handleSaveServer = async (server: Server) => {
    console.log('Save server:', server)
    await updateServer(server)
    await fetchServers()
}

const handleCreateServer = async (server: Omit<Server, 'id'>) => {
    console.log('Create server:', server)
    await createServer(server)
    await fetchServers()
}

const handleSyncAll = async () => {
    console.log('Sync all servers')
    await fetchServers()
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
                <!-- Toggle for deleted servers -->
                <div class="d-flex justify-start mb-4">
                    <v-switch
                        v-model="showDeleted"
                        :label="t('servers.showDeleted')"
                        color="info"
                        hide-details
                    ></v-switch>
                </div>

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
                    :items="filteredServers"
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

        <!-- Modals -->
        <ServerDetailsModal
            v-model="showDetailsModal"
            :server="selectedServer"
            @edit="handleEditFromDetails"
        />
        <ServerEditModal
            v-model="showEditModal"
            :server="selectedServer"
            @save="handleSaveServer"
        />
        <ServerCreateModal v-model="showCreateModal" @create="handleCreateServer" />
    </v-container>
</template>
