// directives/clickOutside.ts
import type { Directive } from 'vue'

export const vClickOutside: Directive = {
    mounted(el, binding) {
        el.clickOutsideEvent = (event: Event) => {
            if (!(el === event.target || el.contains(event.target as Node))) {
                binding.value(event)
            }
        }
        document.addEventListener('click', el.clickOutsideEvent)
    },
    unmounted(el) {
        document.removeEventListener('click', el.clickOutsideEvent)
    },
}
