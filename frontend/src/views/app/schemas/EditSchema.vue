<template>
    <v-card class="mt-5">
        <v-card-title class="d-flex justify-space-between align-center bg-surface-variant">
            <span class="text-h5">{{ $t('actions.edit') }}</span>
        </v-card-title>
        <v-card-text class="overflow-y-auto grow pt-5">
            <v-overlay
                :model-value="schemaStore.loading || deviceTypesLoading || !updateSchemaInput"
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

            <v-form v-if="updateSchemaInput" @submit.prevent="handleUpdate">
                <!-- Preview Modal -->
                <v-dialog v-model="previewDialog" max-width="800">
                    <v-card>
                        <v-card-title class="d-flex justify-space-between align-center">
                            {{ $t('schemas.columns.preview') }}
                            <v-btn icon @click="previewDialog = false">
                                <v-icon>mdi-close</v-icon>
                            </v-btn>
                        </v-card-title>
                        <v-card-text>
                            <v-img
                                v-if="schemaStore.currentSchema?.preview"
                                :src="schemaStore.currentSchema.preview"
                                contain
                            />
                        </v-card-text>
                    </v-card>
                </v-dialog>

                <v-text-field
                    v-model="updateSchemaInput.name"
                    :label="$t('schemas.columns.name')"
                    variant="outlined"
                    class="mb-4"
                />

                <v-row>
                    <v-col cols="12" md="4">
                        <v-select
                            v-model="updateSchemaInput.type"
                            :items="schemaTypeItems"
                            :label="$t('schemas.columns.schema_type')"
                            variant="outlined"
                        />
                    </v-col>
                    <v-col cols="12" md="4">
                        <v-select
                            v-model="updateSchemaInput.device_type_id"
                            :items="deviceTypeItems"
                            :label="$t('schemas.columns.device_type')"
                            variant="outlined"
                        />
                    </v-col>
                    <v-col cols="12" md="4">
                        <v-select
                            v-model="updateSchemaInput.software_id"
                            :items="softwareItems"
                            :label="$t('schemas.columns.software')"
                            variant="outlined"
                        />
                    </v-col>
                </v-row>

                <v-textarea
                    v-model="updateSchemaInput.note"
                    :label="$t('schemas.columns.note')"
                    variant="outlined"
                    rows="4"
                    class="mb-4"
                />

                <v-row>
                    <v-col cols="12" md="6">
                        <div class="d-flex ga-2">
                            <v-file-input
                                v-model="schemaFile"
                                :label="$t('schemas.columns.schema')"
                                variant="outlined"
                                accept="*"
                                prepend-icon="mdi-paperclip"
                                class="grow"
                                @update:model-value="handleSchemaFileChange"
                            />
                            <v-btn
                                v-if="schemaStore.currentSchema?.schema"
                                color="success"
                                icon
                                @click="handleDownloadSchema"
                            >
                                <v-icon>mdi-download</v-icon>
                            </v-btn>
                        </div>
                    </v-col>
                    <v-col cols="12" md="6">
                        <div class="d-flex ga-2">
                            <v-file-input
                                v-model="previewFile"
                                :label="$t('schemas.columns.preview')"
                                variant="outlined"
                                accept="image/*"
                                prepend-icon="mdi-image"
                                class="grow"
                                @update:model-value="handlePreviewFileChange"
                            />
                            <v-btn
                                v-if="schemaStore.currentSchema?.preview"
                                color="warning"
                                icon
                                @click="previewDialog = true"
                            >
                                <v-icon>mdi-image</v-icon>
                            </v-btn>
                        </div>
                    </v-col>
                </v-row>

                <SchemaFormArguments
                    v-if="updateSchemaInput.device_type_id !== -1"
                    :schema-arguments="updateSchemaInput.arguments"
                    :output-values="currentOutputValues"
                    @change="handleArgumentsChange"
                />
                <v-alert v-else type="info" class="text-center">
                    {{ $t('schemas.device_type_warning') }}
                </v-alert>

                <div class="d-flex justify-end mt-4 ga-2">
                    <v-btn color="secondary" @click="$router.back()">
                        {{ $t('actions.back') }}
                    </v-btn>
                    <v-btn
                        v-if="updateSchemaInput.device_type_id !== -1"
                        color="primary"
                        type="submit"
                        :loading="schemaStore.loading"
                    >
                        {{ $t('actions.save') }}
                    </v-btn>
                </div>
            </v-form>
        </v-card-text>
    </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useSchemaStore } from '@/stores/schemaStore'
import type { UpdateSchemaInput, ArgumentInput } from '@/types/api.ts'
import SchemaFormArguments from '@/views/app/schemas/components/SchemaFormArguments.vue'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const schemaStore = useSchemaStore()

const deviceTypesLoading = ref(false)
const schemaFile = ref<File[]>([])
const previewFile = ref<File[]>([])
const previewDialog = ref(false)
const updateSchemaInput = ref<UpdateSchemaInput | null>(null)

const schemaTypeItems = computed(() => [
    { title: t('schemas.types.control'), value: 'control' },
    { title: t('schemas.types.ident'), value: 'ident' },
])

const deviceTypeItems = computed(() => [
    { title: '', value: '-1' },
    ...schemaStore.deviceTypes.map((dt) => ({
        title: dt.name,
        value: dt.id,
    })),
])

const softwareItems = computed(() => [
    { title: '', value: '-1' },
    ...schemaStore.software.map((sw) => ({
        title: sw.name,
        value: sw.id,
    })),
])

const currentOutputValues = computed(() => {
    if (!updateSchemaInput.value || updateSchemaInput.value.device_type_id === -1) return []
    return schemaStore.outputValuesForDeviceType(updateSchemaInput.value.device_type_id)
})

const handleSchemaFileChange = (files: File | File[]) => {
    const fileArray = Array.isArray(files) ? files : files ? [files] : []
    if (updateSchemaInput.value) {
        updateSchemaInput.value.schema = fileArray.length > 0 && fileArray[0] ? fileArray[0] : null
    }
}

const handlePreviewFileChange = (files: File | File[]) => {
    const fileArray = Array.isArray(files) ? files : files ? [files] : []
    if (updateSchemaInput.value) {
        updateSchemaInput.value.preview = fileArray.length > 0 ? fileArray[0] : null
    }
}

const handleArgumentsChange = (args: ArgumentInput[]) => {
    if (updateSchemaInput.value) {
        updateSchemaInput.value.arguments = args
    }
}

const handleDownloadSchema = async () => {
    if (!schemaStore.currentSchema?.schema) {
        alert(t('schemas.download.error'))
        return
    }

    try {
        const response = await fetch(schemaStore.currentSchema.schema)
        const blob = await response.blob()
        const fileExt = schemaStore.currentSchema.schema.split('.').pop()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${schemaStore.currentSchema.name}.${fileExt}`
        a.click()
        window.URL.revokeObjectURL(url)
        alert(t('schemas.download.success'))
    } catch (error) {
        alert(t('schemas.download.error'))
    }
}

const handleUpdate = async () => {
    if (!updateSchemaInput.value) return

    try {
        await schemaStore.updateSchema(updateSchemaInput.value)
        alert(t('schemas.update.success'))
        router.push('/app/schemas')
    } catch (error) {
        alert(t('schemas.update.error'))
    }
}

onMounted(async () => {
    const schemaIdParam = route.params.id
    const schemaId = Array.isArray(schemaIdParam) ? Number(schemaIdParam[0]) : Number(schemaIdParam)
    deviceTypesLoading.value = true

    try {
        await Promise.all([
            schemaStore.fetchSchema(schemaId),
            schemaStore.fetchDeviceTypesAndSoftware(),
        ])

        if (schemaStore.currentSchema) {
            console.log(schemaStore.currentSchema)
            updateSchemaInput.value = {
                id: schemaStore.currentSchema.id,
                name: schemaStore.currentSchema.name,
                type: schemaStore.currentSchema.type,
                device_type_id: schemaStore.currentSchema.device_type_id,
                software_id: schemaStore.currentSchema.software_id,
                note: schemaStore.currentSchema.note,
                arguments: schemaStore.currentSchema.arguments.map((arg) => ({
                    name: arg.name,
                    label: arg.label,
                    default_value: arg.default_value,
                    row: arg.row,
                    order: arg.order,
                    options: arg.options?.map((opt) => ({
                        name: opt.name || '',
                        value: opt.value || '0',
                        output_value: opt.output_value || '',
                    })),
                })),
                schema: null,
                preview: null,
            }
        }
    } finally {
        deviceTypesLoading.value = false
    }
})
</script>
