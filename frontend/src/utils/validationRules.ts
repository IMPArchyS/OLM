import i18n from '@/lib/i18n';

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const hasValue = (value: unknown) => {
    if (Array.isArray(value)) {
        return value.length > 0;
    }

    return !!value;
};

const requiredMessage = (fieldLabel?: string) => {
    if (fieldLabel) {
        return i18n.global.t('validation.requiredWithField', { field: fieldLabel }).toString();
    }

    return i18n.global.t('validation.required').toString();
};

const rules = {
    required: (value: unknown) => hasValue(value) || requiredMessage(),
    requiredFor: (fieldLabel: string) => (value: unknown) => hasValue(value) || requiredMessage(fieldLabel),
    requiredFile: (value: unknown) => hasValue(value) || requiredMessage(),
    validEmail: (value: string) => emailRegex.test(value) || i18n.global.t('validation.invalidFormat').toString(),
};

export default rules;
