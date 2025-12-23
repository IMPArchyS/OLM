<script setup lang="ts">
import { watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useDevices } from '@/composables/useDevices';
import type { Server } from '@/types/api';

const { t } = useI18n();

const props = defineProps<{
    selectedServer: Server | null;
}>();

const { devices, loading, error, fetchDevicesByServer, deviceSoftwareMap } = useDevices();

// Create devices with software for display
const devicesWithSoftware = computed(() => {
    return devices.value.map((device) => ({
        ...device,
        software: deviceSoftwareMap.value[device.id] || [],
    }));
});

watch(
    () => props.selectedServer,
    async (newServer) => {
        if (newServer) {
            await fetchDevicesByServer(newServer.id);
        }
    },
);
</script>

<template>
    <v-container fluid>
        <v-card>
            <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
                <div>
                    <span class="text-h5">{{ t('devices.title') }}</span>
                    <div v-if="selectedServer" class="text-caption text-medium-emphasis">
                        {{ selectedServer.name }}
                    </div>
                </div>
            </v-card-title>

            <v-divider></v-divider>

            <v-card-text>
                <!-- No server selected state -->
                <v-alert
                    v-if="!selectedServer"
                    type="info"
                    variant="tonal"
                    icon="mdi-information-outline"
                    class="ma-4"
                >
                    {{ t('devices.selectServer') }}
                </v-alert>

                <!-- Devices table -->
                <v-data-table
                    v-else
                    :headers="[
                        { title: t('devices.id'), key: 'id', sortable: true },
                        { title: t('devices.name'), key: 'name', sortable: true },
                        { title: t('devices.type'), key: 'device_type.name', sortable: true },
                        { title: t('devices.software'), key: 'software', sortable: false },
                    ]"
                    :items="devicesWithSoftware"
                    :loading="loading"
                    :loading-text="t('devices.loadingDevices')"
                    class="elevation-1"
                    item-value="id"
                >
                    <!-- Software Column -->
                    <template v-slot:item.software="{ item }">
                        <v-chip-group v-if="item.software && item.software.length > 0">
                            <v-chip
                                v-for="software in item.software"
                                :key="software.id"
                                size="small"
                                color="primary"
                                variant="outlined"
                            >
                                {{ software.name }}
                            </v-chip>
                        </v-chip-group>
                        <span v-else class="text-medium-emphasis text-caption">—</span>
                    </template>

                    <!-- No Data -->
                    <template v-slot:no-data>
                        <v-alert type="info" variant="tonal" class="ma-4">
                            {{ t('devices.noDevicesFound') }}
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
