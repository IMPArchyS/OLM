<script setup lang="ts">
defineProps<{ experiment: any }>()
</script>

<template>
    <div>
        <h3>Ongoing Experiment</h3>
        <pre>{{ experiment }}</pre>
    </div>
</template>
