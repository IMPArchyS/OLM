<script lang="ts" setup>
import { useRoles } from '@/composables/useRoles';
import router from '@/router';
import type { Role } from '@/types/api';
import { onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const { roles, loading, error, fetchRoles } = useRoles();

const page = ref(1);
const size = ref(10);

onMounted(async () => {
    await fetchRoles();
});

const handleView = (item: Role) => {
    router.push(`/app/roles/${item.id}/show`);
};

const handleDelete = (item: Role) => {
    // TODO
};
</script>
<template>
    <v-card-text>
        <v-data-table
            v-model:page="page"
            v-model:items-per-page="size"
            :headers="[
                {
                    title: t('roles.id'),
                    key: 'id',
                    sortable: true,
                },
                {
                    title: t('roles.name'),
                    key: 'name',
                    sortable: true,
                },
                {
                    title: t('roles.description'),
                    key: 'description',
                    sortable: true,
                },
                {
                    title: t('roles.actions'),
                    key: 'actions',
                },
            ]"
            :items="roles"
            :loading="loading"
            :loading-text="t('roles.loadingRoles')"
            class="elevation-1"
            item-value="id"
        >
            <!-- Actions Column -->
            <template v-slot:item.actions="{ item }">
                <v-btn icon="mdi-pencil" size="small" variant="text" color="primary" @click="handleView(item)"></v-btn>
                <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="handleDelete(item)"></v-btn>
            </template>

            <template v-slot:no-data>
                <v-alert type="info" variant="tonal" class="ma-4">
                    {{ t('roles.noRoles') }}
                </v-alert>
            </template>
        </v-data-table>
    </v-card-text>
</template>
