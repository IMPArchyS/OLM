<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSchemaStore } from '@/stores/schemaStore'
import { Trashed } from '@/types/api.ts'

const { t } = useI18n()
const schemaStore = useSchemaStore()

const canCreate = ref(true)
const canShow = ref(true)
const canUpdate = ref(true)
const canDelete = ref(true)
const canRestore = ref(true)

const withTrashed = ref<Trashed>(Trashed.Without)
const previewDialog = ref(false)
const previewUrl = ref<string | null>(null)

const trashedOptions = computed(() => [
    { title: t('schemas.trashed.without'), value: Trashed.Without },
    { title: t('schemas.trashed.with'), value: Trashed.With },
    { title: t('schemas.trashed.only'), value: Trashed.Only },
])

const headers = computed(() => [
    {
        title: t('schemas.columns.id'),
        key: 'id',
        width: 80,
    },
    {
        title: t('schemas.columns.name'),
        key: 'name',
    },
    {
        title: t('schemas.columns.device_type'),
        key: 'deviceType.name',
    },
    {
        title: t('schemas.columns.software'),
        key: 'software.name',
    },
    {
        title: t('actions.title'),
        key: 'actions',
        sortable: false,
        width: 200,
    },
])

const handleTrashedChange = async () => {
    await schemaStore.fetchSchemas(withTrashed.value)
}

const handleOpenPreview = (id: number) => {
    const schema = schemaStore.schemas.find((s) => s.id === id)
    if (!schema?.preview) {
        alert(t('schemas.preview.error'))
        return
    }
    previewUrl.value = schema.preview
    previewDialog.value = true
}

const closePreview = () => {
    previewDialog.value = false
    previewUrl.value = null
}

const handleDownload = async (id: number) => {
    const schema = schemaStore.schemas.find((s) => s.id === id)
    if (!schema?.schema) {
        alert(t('schemas.download.error'))
        return
    }

    try {
        const response = await fetch(schema.schema)
        const blob = await response.blob()
        const fileExt = schema.schema.split('.').pop()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${schema.name}.${fileExt}`
        a.click()
        window.URL.revokeObjectURL(url)
        alert(t('schemas.download.success'))
    } catch (error) {
        alert(t('schemas.download.error'))
    }
}

const handleDelete = async (id: number) => {
    if (!confirm(t('schemas.delete.confirm'))) return

    try {
        await schemaStore.deleteSchema(id)
        await schemaStore.fetchSchemas(withTrashed.value)
        alert(t('schemas.delete.success'))
    } catch (error) {
        alert(t('schemas.delete.error'))
    }
}

const handleRestore = async (id: number) => {
    if (!confirm(t('schemas.restore.confirm'))) return

    try {
        await schemaStore.restoreSchema(id)
        await schemaStore.fetchSchemas(withTrashed.value)
        alert(t('schemas.restore.success'))
    } catch (error) {
        alert(t('schemas.restore.error'))
    }
}

onMounted(async () => {
    await schemaStore.fetchSchemas(withTrashed.value)
})
</script>

<template>
    <v-card>
        <v-card-title class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
                <v-icon class="me-2">mdi-calculator</v-icon>
                {{ $t('schemas.index.title') }}
            </div>
            <v-btn
                v-if="canCreate"
                color="primary"
                prepend-icon="mdi-plus"
                @click="$router.push('/app/schemas/create')"
            >
                {{ $t('actions.add') }}
            </v-btn>
        </v-card-title>
        <v-card-text>
            <v-overlay
                :model-value="schemaStore.loading"
                contained
                class="align-center justify-center"
            >
                <v-progress-circular indeterminate size="64" />
            </v-overlay>

            <v-alert
                v-if="schemaStore.error"
                type="error"
                class="mb-4"
                closable
                @click:close="schemaStore.error = null"
            >
                {{ schemaStore.error }}
            </v-alert>

            <v-select
                v-model="withTrashed"
                :items="trashedOptions"
                :label="$t('schemas.trashed.label')"
                variant="outlined"
                density="compact"
                class="mb-4"
                style="max-width: 300px"
                @update:model-value="handleTrashedChange"
            />

            <v-divider class="mb-4" />

            <!-- Preview Modal -->
            <v-dialog v-model="previewDialog" max-width="800">
                <v-card>
                    <v-card-title class="d-flex justify-space-between align-center">
                        {{ $t('schemas.columns.preview') }}
                        <v-btn icon @click="closePreview">
                            <v-icon>mdi-close</v-icon>
                        </v-btn>
                    </v-card-title>
                    <v-card-text>
                        <v-img v-if="previewUrl" :src="previewUrl" contain />
                    </v-card-text>
                </v-card>
            </v-dialog>

            <v-data-table
                :headers="headers"
                :items="schemaStore.schemas"
                :items-per-page="10"
                class="elevation-1"
            >
                <template #item.actions="{ item }">
                    <div class="d-flex ga-2">
                        <v-btn
                            v-if="canShow"
                            color="warning"
                            icon
                            size="small"
                            @click="handleOpenPreview(item.id)"
                        >
                            <v-icon size="small">mdi-image</v-icon>
                        </v-btn>
                        <v-btn
                            v-if="canShow"
                            color="success"
                            icon
                            size="small"
                            @click="handleDownload(item.id)"
                        >
                            <v-icon size="small">mdi-download</v-icon>
                        </v-btn>
                        <v-btn
                            v-if="canUpdate && !item.deleted_at"
                            color="primary"
                            icon
                            size="small"
                            @click="$router.push(`/app/schemas/${item.id}/edit`)"
                        >
                            <v-icon size="small">mdi-pencil</v-icon>
                        </v-btn>
                        <v-btn
                            v-if="canDelete && !item.deleted_at"
                            color="error"
                            icon
                            size="small"
                            @click="handleDelete(item.id)"
                        >
                            <v-icon size="small">mdi-delete</v-icon>
                        </v-btn>
                        <v-btn
                            v-if="canRestore && item.deleted_at"
                            color="grey-darken-2"
                            icon
                            size="small"
                            @click="handleRestore(item.id)"
                        >
                            <v-icon size="small">mdi-undo</v-icon>
                        </v-btn>
                    </div>
                </template>
            </v-data-table>
        </v-card-text>
    </v-card>
</template>
