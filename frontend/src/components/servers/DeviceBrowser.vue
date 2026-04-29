<script setup lang="ts">
import { watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useDevices } from '@/composables/useDevices';
import { useToastStore } from '@/stores/toast';
import type { Server } from '@/types/api';

const { t } = useI18n();

const props = defineProps<{
    selectedServer: Server | null;
    showDeleted: boolean;
}>();

const { devices, loading, fetchDevicesByServer } = useDevices();
const toast = useToastStore();

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
            const result = await fetchDevicesByServer(newServer.id);
            if (!result.success) {
                toast.error(result.message || t('common.error'));
            }
        }
    },
);
</script>

<template>
    <v-data-table
        v-if="selectedServer"
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

    </v-data-table>

</template>
