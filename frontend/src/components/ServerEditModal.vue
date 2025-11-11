<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Server } from '@/types/api'

const { t } = useI18n()

const props = defineProps<{
    modelValue: boolean
    server: Server | null
}>()

const emit = defineEmits<{
    'update:modelValue': [value: boolean]
    save: [server: Server]
}>()

const dialog = computed({
    get: () => props.modelValue,
    set: (value) => emit('update:modelValue', value),
})

// Form data
const formData = ref<Server>({
    id: 0,
    name: '',
    ip_address: '',
    api_domain: '',
    websocket_port: 8080,
    available: false,
    production: false,
    enabled: false,
})

// Watch for server changes to populate form
watch(
    () => props.server,
    (newServer) => {
        if (newServer) {
            formData.value = { ...newServer }
        }
    },
    { immediate: true },
)

// Form validation
const valid = ref(false)
const nameRules = [(v: string) => !!v || `${t('servers.name')} ${t('validation.required')}`]
const ipRules = [
    (v: string) => !!v || `${t('servers.ipAddress')} ${t('validation.required')}`,
    (v: string) => {
        const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/
        return ipPattern.test(v) || t('validation.invalidIpFormat')
    },
]
const domainRules = [(v: string) => !!v || `${t('servers.apiDomain')} ${t('validation.required')}`]
const portRules = [
    (v: number) => !!v || `${t('servers.wsPort')} ${t('validation.required')}`,
    (v: number) => (v > 0 && v <= 65535) || t('validation.invalidPortRange'),
]

const handleSave = () => {
    if (valid.value) {
        emit('save', { ...formData.value })
        dialog.value = false
    }
}

const handleCancel = () => {
    dialog.value = false
}
</script>

<template>
    <v-dialog v-model="dialog" max-width="700px" persistent>
        <v-card v-if="server">
            <v-card-title class="bg-surface-variant">
                <span class="text-h5">{{ t('servers.editServer') }}</span>
            </v-card-title>

            <v-divider></v-divider>

            <v-card-text class="pt-4">
                <v-form v-model="valid">
                    <v-row dense>
                        <!-- Name -->
                        <v-col cols="12" sm="6">
                            <v-text-field
                                v-model="formData.name"
                                :label="t('servers.name')"
                                :rules="nameRules"
                                variant="outlined"
                                density="comfortable"
                                required
                            ></v-text-field>
                        </v-col>

                        <!-- IP Address -->
                        <v-col cols="12" sm="6">
                            <v-text-field
                                v-model="formData.ip_address"
                                :label="t('servers.ipAddress')"
                                :rules="ipRules"
                                variant="outlined"
                                density="comfortable"
                                required
                            ></v-text-field>
                        </v-col>

                        <!-- API Domain -->
                        <v-col cols="12" sm="8">
                            <v-text-field
                                v-model="formData.api_domain"
                                :label="t('servers.apiDomain')"
                                :rules="domainRules"
                                variant="outlined"
                                density="comfortable"
                                required
                            ></v-text-field>
                        </v-col>

                        <!-- WebSocket Port -->
                        <v-col cols="12" sm="4">
                            <v-text-field
                                v-model.number="formData.websocket_port"
                                label="WebSocket Port"
                                :rules="portRules"
                                type="number"
                                variant="outlined"
                                density="comfortable"
                                required
                            ></v-text-field>
                        </v-col>

                        <!-- Status Switches -->
                        <v-col cols="12">
                            <v-divider class="my-2"></v-divider>
                            <div class="text-subtitle-2 mb-3">Status Settings</div>
                        </v-col>

                        <!-- Available -->
                        <v-col cols="12" sm="4">
                            <v-switch
                                v-model="formData.available"
                                :label="t('servers.available')"
                                color="success"
                                hide-details
                            ></v-switch>
                        </v-col>

                        <!-- Production -->
                        <v-col cols="12" sm="4">
                            <v-switch
                                v-model="formData.production"
                                :label="t('servers.production')"
                                color="success"
                                hide-details
                            ></v-switch>
                        </v-col>

                        <!-- Enabled -->
                        <v-col cols="12" sm="4">
                            <v-switch
                                v-model="formData.enabled"
                                :label="t('servers.enabled')"
                                color="success"
                                hide-details
                            ></v-switch>
                        </v-col>
                    </v-row>
                </v-form>
            </v-card-text>

            <v-divider></v-divider>

            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="grey" variant="text" @click="handleCancel">
                    {{ t('reservations.cancel') }}
                </v-btn>
                <v-btn color="primary" variant="elevated" :disabled="!valid" @click="handleSave">
                    {{ t('reservations.save') }}
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>
