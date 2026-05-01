import { ref } from 'vue';
import { useToastStore } from '@/stores/toast';

export function useToastDedup() {
    const toast = useToastStore();
    const lastSignature = ref('');
    const lastTime = ref(0);

    return (level: 'info' | 'success' | 'warning' | 'error', message: string, minGapMs = 1500) => {
        const now = Date.now();
        const sig = `${level}:${message}`;
        if (lastSignature.value === sig && now - lastTime.value < minGapMs) return;
        lastSignature.value = sig;
        lastTime.value = now;
        toast[level](message);
    };
}
