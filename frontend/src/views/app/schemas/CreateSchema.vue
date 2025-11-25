<template>
    <v-card class="h-screen overflow-hidden flex flex-col">
        <v-card-title class="d-flex align-center shrink-0">
            <v-icon class="me-2">mdi-calculator</v-icon>
            {{ $t('actions.create') }}
        </v-card-title>
        <v-card-text class="overflow-y-auto grow">
            <v-form @submit.prevent="handleCreate">
                <v-overlay
                    :model-value="schemaStore.loading || deviceTypesLoading"
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

                <v-text-field
                    v-model="createSchemaInput.name"
                    :label="$t('schemas.columns.name')"
                    variant="outlined"
                    class="mb-4"
                />

                <v-row>
                    <v-col cols="12" md="4">
                        <v-select
                            v-model="createSchemaInput.type"
                            :items="schemaTypeItems"
                            :label="$t('schemas.columns.schema_type')"
                            variant="outlined"
                        />
                    </v-col>
                    <v-col cols="12" md="4">
                        <v-select
                            v-model="createSchemaInput.device_type_id"
                            :items="deviceTypeItems"
                            :label="$t('schemas.columns.device_type')"
                            variant="outlined"
                        />
                    </v-col>
                    <v-col cols="12" md="4">
                        <v-select
                            v-model="createSchemaInput.software_id"
                            :items="softwareItems"
                            :label="$t('schemas.columns.software')"
                            variant="outlined"
                        />
                    </v-col>
                </v-row>

                <v-textarea
                    v-model="createSchemaInput.note"
                    :label="$t('schemas.columns.note')"
                    variant="outlined"
                    rows="4"
                    class="mb-4"
                />

                <v-row>
                    <v-col cols="12" md="6">
                        <v-file-input
                            v-model="schemaFile"
                            :label="$t('schemas.columns.schema')"
                            variant="outlined"
                            accept="*"
                            prepend-icon="mdi-paperclip"
                            @update:model-value="handleSchemaFileChange"
                        />
                    </v-col>
                    <v-col cols="12" md="6">
                        <v-file-input
                            v-model="previewFile"
                            :label="$t('schemas.columns.preview')"
                            variant="outlined"
                            accept="image/*"
                            prepend-icon="mdi-image"
                            @update:model-value="handlePreviewFileChange"
                        />
                    </v-col>
                </v-row>

                <SchemaFormArguments
                    v-if="createSchemaInput.device_type_id !== -1"
                    :schema-arguments="createSchemaInput.arguments"
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
                        v-if="createSchemaInput.device_type_id !== -1"
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
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useSchemaStore } from '@/stores/schemaStore'
import type { CreateSchemaInput, ArgumentInput } from '@/types/api.ts'
import SchemaFormArguments from '@/views/app/schemas/components/SchemaFormArguments.vue'

const router = useRouter()
const { t } = useI18n()
const schemaStore = useSchemaStore()

const deviceTypesLoading = ref(false)
const schemaFile = ref<File[]>([])
const previewFile = ref<File[]>([])

const createSchemaInput = ref<CreateSchemaInput>({
    name: '',
    type: '-1',
    device_type_id: -1,
    software_id: -1,
    note: null,
    arguments: [],
    schema: null,
    preview: null,
})

const schemaTypeItems = computed(() => [
    { title: '', value: '-1' },
    ...schemaStore.availableSchemaTypes.map((type) => ({
        title: t(`schemas.types.${type}`),
        value: type,
    })),
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
    if (createSchemaInput.value.device_type_id === -1) return []
    return schemaStore.outputValuesForDeviceType(createSchemaInput.value.device_type_id)
})

const handleSchemaFileChange = (files: File | File[]) => {
    if (Array.isArray(files)) {
        createSchemaInput.value.schema =
            files.length > 0 && files[0] !== undefined ? files[0] : null
    } else {
        createSchemaInput.value.schema = files !== undefined ? files : null
    }
}

const handlePreviewFileChange = (files: File | File[]) => {
    if (Array.isArray(files)) {
        createSchemaInput.value.preview = files.length > 0 ? files[0] : null
    } else {
        createSchemaInput.value.preview = files ?? null
    }
}

const handleArgumentsChange = (args: ArgumentInput[]) => {
    createSchemaInput.value.arguments = args
}

const handleCreate = async () => {
    try {
        await schemaStore.createSchema(createSchemaInput.value)
        // Show success toast (you'll need to implement toast functionality)
        alert(t('schemas.create.success'))
        router.push('/app/schemas')
    } catch (error) {
        // Error is already set in store
        alert(t('schemas.create.error'))
    }
}

onMounted(async () => {
    deviceTypesLoading.value = true
    try {
        await Promise.all([
            schemaStore.fetchDeviceTypesAndSoftware(),
            schemaStore.fetchAvailableSchemaTypes(),
        ])

        // Set initial values after data is loaded
        if (schemaStore.deviceTypes.length > 0 && schemaStore.deviceTypes[0]?.id !== undefined) {
            createSchemaInput.value.device_type_id = schemaStore.deviceTypes[0].id
        }
        if (schemaStore.software.length > 0 && schemaStore.software[0]?.id !== undefined) {
            createSchemaInput.value.software_id = schemaStore.software[0].id
        }
    } finally {
        deviceTypesLoading.value = false
    }
})
</script>
