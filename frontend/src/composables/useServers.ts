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

    async function updateServer(server: Server) {
        try {
            const response = await fetch(`http://localhost:8000/api/server/${server.id}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(server),
            })

            if (!response.ok) {
                const errorData = await response.json()
                alert(`Failed to update reservation: ${errorData.message || response.statusText}`)
                return
            }
        } catch (e) {
            console.error(`Error updating servers:`, e)
        }
    }

    async function getServer(server: Server): Promise<void> {
        try {
            const response = await fetch(`http://localhost:8000/api/server/${server.id}`)

            if (response.ok) {
                const fetchedServer: Server = await response.json()
                const index = servers.value.findIndex((s) => s.id === server.id)
                if (index !== -1) {
                    servers.value[index] = fetchedServer
                }
            } else {
                console.error(`Failed to fetch server with id`)
            }
        } catch (e) {
            console.error(`Error fetching server with id:`, e)
        }
    }

    async function createServer(server: Omit<Server, 'id'>): Promise<void> {
        try {
            const response = await fetch(`http://localhost:8000/api/server/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(server),
            })

            if (!response.ok) {
                const errorData = await response.json()
                alert(`Failed to create server: ${errorData.message || response.statusText}`)
                return
            }

            // Optionally, you can add the new server to the list immediately
            const newServer: Server = await response.json()
            servers.value.push(newServer)
        } catch (e) {
            console.error(`Error creating server:`, e)
            alert('Error creating server')
        }
    }

    async function softDeleteServer(server: Server) {
        try {
            const response = await fetch(`http://localhost:8000/api/server/${server.id}/delete`, {
                method: 'DELETE',
            })

            if (response.ok) {
                console.error(`Server deleted`)
            } else {
                console.error(`Failed to delete server with id`)
            }
        } catch (e) {
            console.error(`Error deleting server with id:`, e)
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
    }
}
