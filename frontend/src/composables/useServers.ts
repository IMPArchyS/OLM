import { ref, computed } from 'vue'
import type { Device, Software, Server } from '@/types/api'

export function useServers() {
    const servers = ref<Server[]>([])
    const loading = ref(false)
    const error = ref<string | null>(null)

    async function fetchServers(): Promise<void> {
        try {
            const response = await fetch(`http://localhost:8000/api/server/`)

            if (response.ok) {
                const fetchedServers: Server[] = await response.json()
                servers.value = fetchedServers
            } else {
                console.error(`Failed to fetch servers`)
                servers.value = []
            }
        } catch (e) {
            console.error(`Error fetching servers:`, e)
            servers.value = []
        }
    }

    return {
        servers,
        loading,
        error,
        fetchServers,
    }
}
