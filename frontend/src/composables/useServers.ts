import { ref } from 'vue';
import type { Server, ServerStatus } from '@/types/api';
import { apiClient } from '../lib/apiClient';
import type { CreateServerForm, EditServerForm } from '@/types/forms';
import { useI18n } from 'vue-i18n';
import { useToastStore } from '@/stores/toast';
import rules from '@/utils/validationRules';

export function useServers() {
    const servers = ref<Server[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);

    const { t } = useI18n();
    const toast = useToastStore();
    const nameRules = [rules.requiredFor(t('common.name'))];
    const ipRules = [rules.requiredFor(t('servers.ipAddress')), rules.validIp];
    const domainRules = [rules.requiredFor(t('servers.apiDomain'))];
    const portRules = [rules.requiredFor(t('servers.port')), rules.validPort];

    async function fetchServers(): Promise<{ success: boolean; message?: string }> {
        try {
            const response = await apiClient.get('/server/');
            servers.value = response.data;
            return { success: true };
        } catch (e: any) {
            console.error('Failed to fetch servers:', e);
            servers.value = [];
            return { success: false, message: t('error.fetch') };
        }
    }

    async function updateServer(server: EditServerForm): Promise<{ success: boolean; message?: string }> {
        try {
            await apiClient.patch(`/server/${server.id}`, server);
            return { success: true };
        } catch (e: any) {
            console.error('Error updating server:', e);
            return { success: false, message: t('error.update') };
        }
    }

    async function getServerById(id: number): Promise<Server | null> {
        try {
            const response = await apiClient.get(`/server/${id}`);
            return response.data;
        } catch (e) {
            console.error(`Error fetching server with id ${id}: `, e);
        }
        return null;
    }

    async function createServer(server: CreateServerForm): Promise<{ success: boolean; message?: string }> {
        try {
            const response = await apiClient.post('/server/', server);
            servers.value.push(response.data);
            return { success: true };
        } catch (e: any) {
            console.error('Error creating server:', e);
            return { success: false, message: t('error.create') };
        }
    }

    async function restoreServer(id: number): Promise<{ success: boolean; message?: string }> {
        try {
            await apiClient.post(`/server/${id}/restore`);
            await fetchServers();
            return { success: true };
        } catch (e: any) {
            console.error(`Error restoring server with id ${id}: `, e);
            return { success: false, message: t('error.restore') };
        }
    }

    async function softDeleteServer(server: Server): Promise<{ success: boolean; message?: string }> {
        try {
            await apiClient.delete(`/server/${server.id}`);
            await fetchServers();
            return { success: true };
        } catch (e: any) {
            console.error('Error deleting server:', e);
            return { success: false, message: t('error.delete') };
        }
    }

    async function syncServer(id: number): Promise<ServerStatus | null> {
        try {
            const response = await apiClient.post(`/server/${id}/sync`);
            return response.data;
        } catch (e: any) {
            console.error(`Error Syncing server with id ${id}: `, e.status);
        }
        return null;
    }

    async function syncAllServers(): Promise<Array<{ id: number; available: boolean; error?: string }> | null> {
        try {
            const response = await apiClient.post('/server/sync_all');
            return response.data;
        } catch (e) {
            console.error('Error syncing all servers:', e);
        }
        return null;
    }

    async function syncServerWithToast(id: number): Promise<ServerStatus | null> {
        const result = await syncServer(id);
        if (result === null) {
            toast.error(t('common.error'));
            return null;
        }
        if (result.available) {
            toast.success(t('servers.synced'));
        } else {
            toast.warning(t('servers.unreachable'));
        }
        return result;
    }

    return {
        servers,
        loading,
        error,
        nameRules,
        ipRules,
        domainRules,
        portRules,
        fetchServers,
        updateServer,
        restoreServer,
        getServerById,
        syncServer,
        syncServerWithToast,
        syncAllServers,
        createServer,
        softDeleteServer,
    };
}
