<template>
    <div class="dashboard">
        <header class="dashboard-header">
            <h1>OVL Central Dashboard</h1>
            <div class="stats-overview">
                <div class="stat-card">
                    <h3>Total Workspaces</h3>
                    <p class="stat-number">{{ stats.totalWorkspaces }}</p>
                </div>
                <div class="stat-card">
                    <h3>Total Tools</h3>
                    <p class="stat-number">{{ stats.totalTools }}</p>
                </div>
                <div class="stat-card">
                    <h3>Active Reservations</h3>
                    <p class="stat-number">{{ stats.activeReservations }}</p>
                </div>
                <div class="stat-card">
                    <h3>Available Tools</h3>
                    <p class="stat-number">{{ stats.availableTools }}</p>
                </div>
            </div>
        </header>

        <main class="dashboard-content">
            <section class="dashboard-section">
                <h2>Recent Activity</h2>
                <div class="activity-list">
                    <div
                        v-for="activity in recentActivity"
                        :key="activity.id"
                        class="activity-item"
                    >
                        <span class="activity-time">{{ formatTime(activity.timestamp) }}</span>
                        <span class="activity-description">{{ activity.description }}</span>
                    </div>
                </div>
            </section>

            <section class="dashboard-section">
                <h2>Quick Actions</h2>
                <div class="quick-actions">
                    <button @click="navigateTo('/workspaces')" class="action-btn">
                        <i class="icon-workspace"></i>
                        Manage Workspaces
                    </button>
                    <button @click="navigateTo('/tools')" class="action-btn">
                        <i class="icon-tools"></i>
                        Manage Tools
                    </button>
                    <button @click="navigateTo('/reservations')" class="action-btn">
                        <i class="icon-calendar"></i>
                        View Reservations
                    </button>
                </div>
            </section>

            <section class="dashboard-section">
                <h2>Workspace Overview</h2>
                <div class="workspace-grid">
                    <div v-for="workspace in workspaces" :key="workspace.id" class="workspace-card">
                        <h3>{{ workspace.name }}</h3>
                        <p>{{ workspace.tools.length }} tools</p>
                        <div class="tool-status">
                            <span class="available"
                                >{{ getAvailableTools(workspace) }} available</span
                            >
                            <span class="occupied">{{ getOccupiedTools(workspace) }} occupied</span>
                        </div>
                    </div>
                </div>
            </section>
        </main>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Types
interface Tool {
    id: number
    name: string
    occupied: boolean
    workspace_id: number
}

interface Workspace {
    id: number
    name: string
    tools: Tool[]
}

interface Activity {
    id: number
    description: string
    timestamp: Date
}

interface Stats {
    totalWorkspaces: number
    totalTools: number
    activeReservations: number
    availableTools: number
}

// Reactive data
const workspaces = ref<Workspace[]>([])
const recentActivity = ref<Activity[]>([])
const stats = ref<Stats>({
    totalWorkspaces: 0,
    totalTools: 0,
    activeReservations: 0,
    availableTools: 0,
})

// Computed properties
const availableTools = computed(() => {
    return workspaces.value.reduce((total, workspace) => {
        return total + workspace.tools.filter((tool) => !tool.occupied).length
    }, 0)
})

// Methods
const fetchDashboardData = async () => {
    try {
        // Fetch workspaces
        const workspaceResponse = await fetch('/api/workspace/')
        const workspaceData = await workspaceResponse.json()
        workspaces.value = workspaceData

        // Fetch tools
        const toolResponse = await fetch('/api/tool/')
        const toolData = await toolResponse.json()

        // Calculate stats
        stats.value = {
            totalWorkspaces: workspaceData.length,
            totalTools: toolData.length,
            activeReservations: 0, // You'll need to implement this endpoint
            availableTools: toolData.filter((tool: Tool) => !tool.occupied).length,
        }

        // Mock recent activity (replace with real API call)
        recentActivity.value = [
            {
                id: 1,
                description: 'New tool "Oscilloscope" added to Workspace A',
                timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
            },
            {
                id: 2,
                description: 'Tool "Multimeter" reservation ended',
                timestamp: new Date(Date.now() - 1000 * 60 * 60), // 1 hour ago
            },
        ]
    } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
    }
}

const getAvailableTools = (workspace: Workspace) => {
    return workspace.tools.filter((tool) => !tool.occupied).length
}

const getOccupiedTools = (workspace: Workspace) => {
    return workspace.tools.filter((tool) => tool.occupied).length
}

const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleString()
}

const navigateTo = (path: string) => {
    router.push(path)
}

// Lifecycle
onMounted(() => {
    fetchDashboardData()
})
</script>

<style scoped>
.dashboard {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.dashboard-header {
    margin-bottom: 30px;
}

.dashboard-header h1 {
    color: #2c3e50;
    margin-bottom: 20px;
}

.stats-overview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.stat-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    text-align: center;
}

.stat-card h3 {
    margin: 0 0 10px 0;
    color: #7f8c8d;
    font-size: 14px;
    text-transform: uppercase;
}

.stat-number {
    margin: 0;
    font-size: 2em;
    font-weight: bold;
    color: #2c3e50;
}

.dashboard-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
}

.dashboard-section {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.dashboard-section h2 {
    margin-top: 0;
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 10px;
}

.activity-list {
    max-height: 300px;
    overflow-y: auto;
}

.activity-item {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid #ecf0f1;
}

.activity-time {
    font-size: 12px;
    color: #7f8c8d;
    min-width: 120px;
}

.activity-description {
    flex: 1;
    margin-left: 15px;
}

.quick-actions {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.action-btn {
    padding: 15px;
    border: none;
    border-radius: 6px;
    background: #3498db;
    color: white;
    cursor: pointer;
    transition: background-color 0.3s;
    display: flex;
    align-items: center;
    gap: 10px;
}

.action-btn:hover {
    background: #2980b9;
}

.workspace-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 15px;
    grid-column: 1 / -1;
}

.workspace-card {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 6px;
    border-left: 4px solid #3498db;
}

.workspace-card h3 {
    margin: 0 0 10px 0;
    color: #2c3e50;
}

.tool-status {
    display: flex;
    gap: 15px;
    font-size: 12px;
    margin-top: 10px;
}

.available {
    color: #27ae60;
}

.occupied {
    color: #e74c3c;
}

@media (max-width: 768px) {
    .dashboard-content {
        grid-template-columns: 1fr;
    }

    .stats-overview {
        grid-template-columns: repeat(2, 1fr);
    }
}
</style>
