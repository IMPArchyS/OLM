<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ExperimentSandbox from '@/components/ExperimentSandbox.vue'

const reservedExperiments = ref([])
const loading = ref(true)

onMounted(async () => {
    loading.value = true
    try {
        const response = await fetch('http://localhost:8000/api/reserved_experiment/')
        if (response.ok) {
            reservedExperiments.value = await response.json()
        } else {
            reservedExperiments.value = []
        }
    } catch (e) {
        reservedExperiments.value = []
    }
    loading.value = false
})
</script>

<template>
    <div class="card bg-base-300!">
        <h2>Dashboard</h2>
        <div v-if="loading">Loading...</div>
        <div v-else>
            <div v-if="reservedExperiments.length > 0">
                <div
                    v-for="(experiment, index) in reservedExperiments"
                    :key="index"
                    class="experiment-container"
                >
                    <ExperimentSandbox :experiment="experiment" />
                </div>
            </div>
            <div v-else>No active experiments.</div>
        </div>
    </div>
</template>

<style scoped>
.experiment-container {
    margin-bottom: 20px;
}
</style>
