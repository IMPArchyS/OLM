import { ref } from 'vue';
import type { Server } from '@/types/api';
import { apiClient } from './useAxios';
import type { CreateServerForm, EditServerForm } from '@/types/forms';
import { useI18n } from 'vue-i18n';

export function useServers() {
    const servers = ref<Server[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);

    const { t } = useI18n();
    const nameRules = [(v: string) => !!v || `${t('servers.name')} ${t('validation.required')}`];

    const ipRules = [
        (v: string) => !!v || `${t('servers.ipAddress')} ${t('validation.required')}`,
        (v: string) => {
            const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
            return ipPattern.test(v) || t('validation.invalidIpFormat');
        },
    ];

    const domainRules = [(v: string) => !!v || `${t('servers.apiDomain')} ${t('validation.required')}`];

    const portRules = [
        (v: number) => !!v || `${t('servers.wsPort')} ${t('validation.required')}`,
        (v: number) => (v > 0 && v <= 65535) || t('validation.invalidPortRange'),
    ];

    async function fetchServers(): Promise<void> {
        try {
            const response = await apiClient.get('/server/');
            servers.value = response.data;
        } catch (e) {
            console.error('Failed to fetch servers:', e);
            servers.value = [];
        }
    }

    async function updateServer(server: EditServerForm): Promise<{ success: boolean; message?: string }> {
        try {
            await apiClient.patch(`/server/${server.id}/`, server);
            return { success: true };
        } catch (e: any) {
            console.error('Error creating server:', e);
            return {
                success: false,
                message: e.response?.data?.message || 'Failed to create server',
            };
        }
    }

    async function getServer(server: Server): Promise<void> {
        try {
            const response = await apiClient.get(`/server/${server.id}`);
            const index = servers.value.findIndex((s) => s.id === server.id);
            if (index !== -1) {
                servers.value[index] = response.data;
            }
        } catch (e) {
            console.error('Error fetching server:', e);
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
            return {
                success: false,
                message: e.response?.data?.message || 'Failed to create server',
            };
        }
    }

    async function restoreServer(id: number): Promise<{ success: boolean; message?: string }> {
        try {
            await apiClient.post(`/server/${id}/restore`);
            return { success: true };
        } catch (e: any) {
            console.error(`Error fetching server with id ${id}: `, e);
            return {
                success: false,
                message: e.response?.data?.message || 'Failed to create server',
            };
        }
    }

    async function softDeleteServer(server: Server) {
        try {
            await apiClient.delete(`/server/${server.id}/delete`);
        } catch (e) {
            console.error('Error deleting server:', e);
            throw e;
        }
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
        getServer,
        getServerById,
        createServer,
        softDeleteServer,
    };
}
