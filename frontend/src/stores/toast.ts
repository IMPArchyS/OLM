import { defineStore } from 'pinia';

export const useToastStore = defineStore('toast', {
    state: () => ({
        message: '',
        color: '',
        show: false,
        delay: 3000,
        icon: null as string | null,
    }),
    actions: {
        showToast(message: string, color = 'info', icon: string | null = null) {
            this.message = message;
            this.color = color;
            this.show = true;
            this.icon = icon;
            setTimeout(() => {
                this.show = false;
            }, this.delay);
        },
        info(message: string) {
            this.showToast(message, 'info', 'mdi-information');
        },
        success(message: string) {
            this.showToast(message, 'success', 'mdi-check');
        },
        error(message: string) {
            this.showToast(message, 'error', 'mdi-alert');
        },
        warning(message: string) {
            this.showToast(message, 'warning', 'mdi-alert');
        },
    },
});
