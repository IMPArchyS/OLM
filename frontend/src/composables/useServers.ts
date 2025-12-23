import { ref } from 'vue';
import type { Server } from '@/types/api';
import { apiClient } from './useAxios';

export function useServers() {
    const servers = ref<Server[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);

    async function fetchServers(): Promise<void> {
        try {
            const response = await apiClient.get('/server/');
            servers.value = response.data;
        } catch (e) {
            console.error('Failed to fetch servers:', e);
            servers.value = [];
        }
    }

    async function updateServer(server: Server) {
        try {
            await apiClient.patch(`/server/${server.id}/`, server);
        } catch (e) {
            console.error('Error updating server:', e);
            throw e;
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

    async function createServer(server: Omit<Server, 'id'>): Promise<void> {
        try {
            const response = await apiClient.post('/server/', server);
            servers.value.push(response.data);
        } catch (e) {
            console.error('Error creating server:', e);
            throw e;
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
        fetchServers,
        updateServer,
        getServer,
        createServer,
        softDeleteServer,
    };
}
