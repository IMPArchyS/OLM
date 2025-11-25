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
        align: 'center' as const,
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
    <v-card class="mt-5">
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ $t('schemas.index.title') }}</span>
            <v-btn
                v-if="canCreate"
                color="primary"
                prepend-icon="mdi-plus"
                @click="$router.push('/app/schemas/create')"
            >
                {{ $t('actions.add') }}
            </v-btn>
        </v-card-title>

        <v-divider></v-divider>

        <v-card-text>
            <!-- Toggle for deleted schemas -->
            <div class="d-flex justify-start mb-4">
                <v-switch
                    v-model="withTrashed"
                    :label="$t('schemas.trashed.label')"
                    color="info"
                    hide-details
                    :true-value="Trashed.With"
                    :false-value="Trashed.Without"
                    @update:model-value="handleTrashedChange"
                ></v-switch>
            </div>

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
                :loading="schemaStore.loading"
                :loading-text="t('common.loading')"
                class="elevation-1"
                item-value="id"
            >
                <template #item.actions="{ item }">
                    <v-btn
                        v-if="canShow"
                        icon="mdi-image"
                        size="small"
                        variant="text"
                        color="warning"
                        @click="handleOpenPreview(item.id)"
                    ></v-btn>
                    <v-btn
                        v-if="canShow"
                        icon="mdi-download"
                        size="small"
                        variant="text"
                        color="success"
                        @click="handleDownload(item.id)"
                    ></v-btn>
                    <v-btn
                        v-if="canUpdate && !item.deleted_at"
                        icon="mdi-pencil"
                        size="small"
                        variant="text"
                        color="primary"
                        @click="$router.push(`/app/schemas/${item.id}/edit`)"
                    ></v-btn>
                    <v-btn
                        v-if="canDelete && !item.deleted_at"
                        icon="mdi-delete"
                        size="small"
                        variant="text"
                        color="error"
                        @click="handleDelete(item.id)"
                    ></v-btn>
                    <v-btn
                        v-if="canRestore && item.deleted_at"
                        icon="mdi-undo"
                        size="small"
                        variant="text"
                        color="grey-darken-2"
                        @click="handleRestore(item.id)"
                    ></v-btn>
                </template>

                <!-- No Data -->
                <template v-slot:no-data>
                    <v-alert type="info" variant="tonal" class="ma-4">
                        {{ t('schemas.noSchemasFound') }}
                    </v-alert>
                </template>
            </v-data-table>

            <!-- Error Alert -->
            <v-alert v-if="schemaStore.error" type="error" variant="tonal" class="mt-4" closable>
                {{ schemaStore.error }}
            </v-alert>
        </v-card-text>
    </v-card>
</template>
