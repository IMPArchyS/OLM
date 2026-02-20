<script lang="ts" setup>
import { useUsers } from '@/composables/useUsers';
import type { User } from '@/types/api';
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const { users, loading, error, total, fetchUsers } = useUsers();

const page = ref(1);
const size = ref(10);

watch(
    [page, size],
    () => {
        fetchUsers(page.value, size.value);
    },
    { immediate: true },
);

const handleEdit = (item: User) => {
    // TODO
};

const handleDelete = (item: User) => {
    // TODO
};
</script>
<template>
    <v-card-text>
        <!-- <v-select
            class="mb-4"
            density="comfortable"
            color="info"
            :label="t('actions.show')"
            :items="[
                { title: t('users.onlyNotDeleted'), value: 'active' },
                { title: t('users.withDeleted'), value: 'all' },
                { title: t('users.onlyDeleted'), value: 'deleted' },
            ]"
            :model-value="'active'"
            variant="outlined"
            hide-details
        /> -->

        <v-data-table
            v-model:page="page"
            v-model:items-per-page="size"
            :items-length="total"
            :headers="[
                {
                    title: t('users.id'),
                    key: 'id',
                    sortable: true,
                },
                {
                    title: t('users.name'),
                    key: 'name',
                    sortable: true,
                },
                {
                    title: t('users.email'),
                    key: 'username',
                    sortable: true,
                },
                {
                    title: t('users.actions'),
                    key: 'actions',
                },
            ]"
            :items="users"
            :loading="loading"
            :loading-text="t('users.loadinUsers')"
            class="elevation-1"
            item-value="id"
        >
            <!-- Actions Column -->
            <template v-slot:item.actions="{ item }">
                <v-btn icon="mdi-pencil" size="small" variant="text" color="primary" @click="handleEdit(item)"></v-btn>
                <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="handleDelete(item)"></v-btn>
            </template>

            <template v-slot:no-data>
                <v-alert type="info" variant="tonal" class="ma-4">
                    {{ t('users.noUsers') }}
                </v-alert>
            </template>
        </v-data-table>
    </v-card-text>
</template>
