// stores/schemaStore.ts
import { defineStore } from 'pinia'
import { apiClient } from '@/composables/useAxios'
import {
    type SchemaBasic,
    type SchemaExtended,
    type CreateSchemaInput,
    type UpdateSchemaInput,
    type DeviceType,
    type Software,
    Trashed,
} from '@/types/api.ts'

interface SchemaState {
    schemas: SchemaBasic[]
    currentSchema: SchemaExtended | null
    deviceTypes: DeviceType[]
    software: Software[]
    availableSchemaTypes: string[]
    loading: boolean
    error: string | null
}

export const useSchemaStore = defineStore('schema', {
    state: (): SchemaState => ({
        schemas: [],
        currentSchema: null,
        deviceTypes: [],
        software: [],
        availableSchemaTypes: [],
        loading: false,
        error: null,
    }),

    getters: {
        outputValuesForDeviceType:
            (state) =>
            (deviceTypeId: number): string[] => {
                const deviceType = state.deviceTypes.find((dt) => dt.id === deviceTypeId)
                if (!deviceType) return []

                const outputValues: string[] = []
                deviceType.experiment.forEach((experiment) => {
                    experiment.output_arguments.forEach((outputArg) => {
                        if (!outputValues.includes(outputArg.name)) {
                            outputValues.push(outputArg.name)
                        }
                    })
                })
                return outputValues
            },
    },

    actions: {
        async fetchSchemas(trashed: Trashed = Trashed.Without) {
            this.loading = true
            this.error = null
            try {
                const response = await apiClient.get<SchemaBasic[]>('/schema/', {
                    // params: { trashed },
                })
                this.schemas = response.data
            } catch (err: any) {
                this.error = err.response?.data?.message || 'Failed to fetch schemas'
                throw err
            } finally {
                this.loading = false
            }
        },

        async fetchSchema(id: number) {
            this.loading = true
            this.error = null
            try {
                const response = await apiClient.get<SchemaExtended>(`/schema/${id}`)
                this.currentSchema = response.data
                return response.data
            } catch (err: any) {
                this.error = err.response?.data?.message || 'Failed to fetch schema'
                throw err
            } finally {
                this.loading = false
            }
        },

        async fetchDeviceTypesAndSoftware() {
            this.loading = true
            this.error = null
            try {
                const [deviceTypesRes, softwareRes] = await Promise.all([
                    apiClient.get<DeviceType[]>('/device_type/'),
                    apiClient.get<Software[]>('/software/'),
                ])
                this.deviceTypes = deviceTypesRes.data
                this.software = softwareRes.data
            } catch (err: any) {
                this.error =
                    err.response?.data?.message || 'Failed to fetch device types and software'
                throw err
            } finally {
                this.loading = false
            }
        },

        async fetchAvailableSchemaTypes() {
            this.loading = true
            this.error = null
            try {
                const response = await apiClient.get<string[]>('/schema/type')
                this.availableSchemaTypes = response.data
            } catch (err: any) {
                this.error = err.response?.data?.message || 'Failed to fetch schema types'
                throw err
            } finally {
                this.loading = false
            }
        },

        async createSchema(input: CreateSchemaInput) {
            this.loading = true
            this.error = null
            try {
                const formData = new FormData()
                formData.append('name', input.name)
                formData.append('type', input.type)
                formData.append('device_type_id', input.device_type_id.toString())
                formData.append('software_id', input.software_id.toString())
                if (input.note) formData.append('note', input.note)
                formData.append('arguments', JSON.stringify(input.arguments))
                if (input.schema) formData.append('schema', input.schema)
                if (input.preview) formData.append('preview', input.preview)

                const response = await apiClient.post<SchemaExtended>('/schema/', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                })
                return response.data
            } catch (err: any) {
                this.error = err.response?.data?.message || 'Failed to create schema'
                throw err
            } finally {
                this.loading = false
            }
        },

        async updateSchema(input: UpdateSchemaInput) {
            this.loading = true
            this.error = null
            try {
                const formData = new FormData()
                formData.append('name', input.name)
                formData.append('type', input.type)
                formData.append('device_type_id', input.device_type_id.toString())
                formData.append('software_id', input.software_id.toString())
                if (input.note) formData.append('note', input.note)
                formData.append('arguments', JSON.stringify(input.arguments))
                if (input.schema) formData.append('schema', input.schema)
                if (input.preview) formData.append('preview', input.preview)

                const response = await apiClient.put<SchemaExtended>(
                    `/schema/${input.id}/`,
                    formData,
                    {
                        headers: { 'Content-Type': 'multipart/form-data' },
                    },
                )
                return response.data
            } catch (err: any) {
                this.error = err.response?.data?.message || 'Failed to update schema'
                throw err
            } finally {
                this.loading = false
            }
        },

        async deleteSchema(id: number) {
            this.loading = true
            this.error = null
            try {
                await apiClient.delete(`/schema/${id}/delete/`)
            } catch (err: any) {
                this.error = err.response?.data?.message || 'Failed to delete schema'
                throw err
            } finally {
                this.loading = false
            }
        },

        async restoreSchema(id: number) {
            this.loading = true
            this.error = null
            try {
                await apiClient.post(`/schema/${id}/restore/`)
            } catch (err: any) {
                this.error = err.response?.data?.message || 'Failed to restore schema'
                throw err
            } finally {
                this.loading = false
            }
        },
    },
})
