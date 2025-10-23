<script setup lang="ts">
// filepath: c:\Users\01dja\Documents\FEI\dp\OLM\frontend\src\components\ExperimentSandbox.vue
defineProps<{ experiment: any }>()
</script>

<template>
    <div>
        <h3>Ongoing Experiment</h3>
        <pre>{{ experiment }}</pre>
        <!-- Add your playground UI here -->
    </div>
</template>
