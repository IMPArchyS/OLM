<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Server } from '@/types/api';

const { t } = useI18n();

const props = defineProps<{
    modelValue: boolean;
    server: Server | null;
}>();

const emit = defineEmits<{
    'update:modelValue': [value: boolean];
    edit: [server: Server];
}>();

const dialog = computed({
    get: () => props.modelValue,
    set: (value) => emit('update:modelValue', value),
});

const handleEdit = () => {
    if (props.server) {
        emit('edit', props.server);
        dialog.value = false;
    }
};
</script>

<template>
    <v-dialog v-model="dialog" max-width="600px">
        <v-card v-if="server">
            <v-card-title class="bg-surface-variant">
                <span class="text-h5">{{ t('servers.viewServer') }}</span>
            </v-card-title>

            <v-divider></v-divider>

            <v-card-text class="pt-4">
                <v-row dense>
                    <!-- ID -->
                    <v-col cols="12" sm="6">
                        <div class="text-caption text-medium-emphasis">{{ t('servers.id') }}</div>
                        <div class="text-body-1">{{ server.id }}</div>
                    </v-col>

                    <!-- Name -->
                    <v-col cols="12" sm="6">
                        <div class="text-caption text-medium-emphasis">{{ t('servers.name') }}</div>
                        <div class="text-body-1">{{ server.name }}</div>
                    </v-col>

                    <!-- IP Address -->
                    <v-col cols="12" sm="6">
                        <div class="text-caption text-medium-emphasis">
                            {{ t('servers.ipAddress') }}
                        </div>
                        <div class="text-body-1">{{ server.ip_address }}</div>
                    </v-col>

                    <!-- API Domain -->
                    <v-col cols="12" sm="6">
                        <div class="text-caption text-medium-emphasis">
                            {{ t('servers.apiDomain') }}
                        </div>
                        <div class="text-body-1">{{ server.api_domain }}</div>
                    </v-col>

                    <!-- WebSocket Port -->
                    <v-col cols="12" sm="6">
                        <div class="text-caption text-medium-emphasis">WebSocket Port</div>
                        <div class="text-body-1">{{ server.websocket_port }}</div>
                    </v-col>

                    <!-- Status Section -->
                    <v-col cols="12">
                        <v-divider class="my-3"></v-divider>
                        <div class="text-subtitle-2 mb-2">Status</div>
                    </v-col>

                    <!-- Available -->
                    <v-col cols="12" sm="4">
                        <div class="d-flex align-center">
                            <v-icon
                                :color="server.available ? 'success' : 'error'"
                                :icon="server.available ? 'mdi-check-circle' : 'mdi-close-circle'"
                                class="mr-2"
                            ></v-icon>
                            <span>{{ t('servers.available') }}</span>
                        </div>
                    </v-col>

                    <!-- Production -->
                    <v-col cols="12" sm="4">
                        <div class="d-flex align-center">
                            <v-icon
                                :color="server.production ? 'success' : 'error'"
                                :icon="server.production ? 'mdi-check-circle' : 'mdi-close-circle'"
                                class="mr-2"
                            ></v-icon>
                            <span>{{ t('servers.production') }}</span>
                        </div>
                    </v-col>

                    <!-- Enabled -->
                    <v-col cols="12" sm="4">
                        <div class="d-flex align-center">
                            <v-icon
                                :color="server.enabled ? 'success' : 'error'"
                                :icon="server.enabled ? 'mdi-check-circle' : 'mdi-close-circle'"
                                class="mr-2"
                            ></v-icon>
                            <span>{{ t('servers.enabled') }}</span>
                        </div>
                    </v-col>
                </v-row>
            </v-card-text>

            <v-divider></v-divider>

            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="primary" variant="text" @click="handleEdit">
                    {{ t('servers.editServer') }}
                </v-btn>
                <v-btn color="grey" variant="text" @click="dialog = false">
                    {{ t('common.close') }}
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>
