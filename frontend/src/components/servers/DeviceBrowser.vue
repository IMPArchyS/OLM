<script setup lang="ts">
import { watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useDevices } from '@/composables/useDevices';
import type { Server } from '@/types/api';

const { t } = useI18n();

const props = defineProps<{
    selectedServer: Server | null;
    showDeleted: boolean;
}>();

const { devices, loading, error, fetchDevicesByServer } = useDevices();

const filteredDevices = computed(() => {
    if (props.showDeleted) {
        return devices.value;
    } else {
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
        :row-props="({ item }) => ({ class: item.deleted_at ? 'text-error' : '' })"
        item-value="id"
    >
        <template v-slot:item.software="{ item }">
            <v-chip class="mr-1" v-for="software in item.softwares" :key="software.id" size="small" variant="outlined">
                {{ software.name }}
            </v-chip>
        </template>

        <template v-slot:no-data>
            <v-alert type="info" variant="tonal" class="ma-4">
                {{ t('devices.noDevicesFound') }}
            </v-alert>
        </template>
    </v-data-table>

    <v-alert v-if="error" type="error" variant="tonal" class="ma-4" closable>
        {{ error }}
    </v-alert>
</template>
