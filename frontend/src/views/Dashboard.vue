<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ExperimentSandbox from '@/components/ExperimentSandbox.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
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
    <div class="card bg-base-300! p-0! rounded-2xl!">
        <div class="card-header">
            <h2 class="text-xl font-semibold py-2.5! px-2.5!">{{ t('dashboard.title') }}</h2>
        </div>
        <div class="card-body bg-base-200 rounded-b-2xl! px-2.5! pt-2! pb-4!">
            <div v-if="loading">{{ t('common.loading') }}</div>
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
                <div v-else>{{ t('dashboard.no_active_experiments') }}</div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.experiment-container {
    margin-bottom: 20px;
}
</style>
