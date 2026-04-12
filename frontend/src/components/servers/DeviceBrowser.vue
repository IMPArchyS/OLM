<script setup lang="ts">
import { watch, computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useDevices } from '@/composables/useDevices';
import type { Server } from '@/types/api';

const { t } = useI18n();

const props = defineProps<{
    selectedServer: Server | null;
}>();

const { devices, loading, error, fetchDevicesByServer } = useDevices();

const showDeletedDevices = ref(false);
const filteredDevices = computed(() => {
    if (showDeletedDevices.value) {
        return devices.value;
    } else {
        console.log(devices.value.filter((device) => !device.deleted_at));
        return devices.value.filter((device) => !device.deleted_at);
    }
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
        <v-alert v-if="!selectedServer" type="info" variant="tonal" icon="mdi-information-outline" class="ma-4">
            {{ t('devices.selectServer') }}
        </v-alert>

        <v-data-table
            v-else
            :headers="[
                { title: t('devices.id'), key: 'id', sortable: true },
                { title: t('devices.name'), key: 'name', sortable: true },
                { title: t('devices.type'), key: 'device_type.name', sortable: true },
                { title: t('devices.software'), key: 'software', sortable: false },
            ]"
            :items="filteredDevices"
            :loading="loading"
            :loading-text="t('devices.loadingDevices')"
            class="elevation-1"
            item-value="id"
        >
            <template #top>
                <v-toolbar flat density="comfortable" class="px-2">
                    <v-toolbar-title class="text-h6">
                        {{ t('servers.devices') + ' server - ' + (selectedServer?.name ?? '') }}
                    </v-toolbar-title>
                    <v-spacer />
                    <v-switch v-model="showDeletedDevices" :label="t('devices.showDeleted')" color="info" hide-details />
                </v-toolbar>
                <v-divider />
            </template>
            <!-- Software Column -->
            <template v-slot:item.software="{ item }">
                <v-chip class="mr-1" v-for="software in item.softwares" :key="software.id" size="small" variant="outlined">
                    {{ software.name }}
                </v-chip>
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
    </v-container>
</template>
