import { ref } from 'vue';

const snackbar = ref(false);
const snackbarText = ref('');
const snackbarColor = ref<'success' | 'error' | 'info' | 'warning'>('success');
const snackbarTimeout = ref(2000);

export function useToast() {
    const showToast = (message: string, color: 'success' | 'error' | 'info' | 'warning' = 'success', timeout: number = 3000) => {
        snackbarText.value = message;
        snackbarColor.value = color;
        snackbarTimeout.value = timeout;
        snackbar.value = true;
    };

    const showSuccess = (message: string, timeout?: number) => {
        showToast(message, 'success', timeout);
    };

    const showError = (message: string, timeout?: number) => {
        showToast(message, 'error', timeout);
    };

    const showInfo = (message: string, timeout?: number) => {
        showToast(message, 'info', timeout);
    };

    const showWarning = (message: string, timeout?: number) => {
        showToast(message, 'warning', timeout);
    };

    const hideToast = () => {
        snackbar.value = false;
    };

    return {
        snackbar,
        snackbarText,
        snackbarColor,
        snackbarTimeout,
        showToast,
        showSuccess,
        showError,
        showInfo,
        showWarning,
        hideToast,
    };
}
