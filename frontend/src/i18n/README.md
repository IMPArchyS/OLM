# Vue I18n Usage Guide

## Setup Complete ✅

Vue I18n has been installed and configured in your project.

## How to Use Translations

### In Vue Components (Composition API)

```vue
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
    <!-- Simple translation -->
    <h1>{{ t('reservations.title') }}</h1>

    <!-- Translation in attributes -->
    <button :title="t('common.save')">Save</button>

    <!-- Translation with parameters -->
    <p>{{ t('welcome', { name: 'John' }) }}</p>
</template>
```

### In TypeScript/JavaScript Files

```typescript
import { useI18n } from 'vue-i18n'

// Inside a composable or function
const { t } = useI18n()
const message = t('common.error')
```

### Global Access (use sparingly)

```typescript
import i18n from '@/i18n'

const message = i18n.global.t('common.error')
```

## Adding New Translations

1. Open `/src/i18n/locales/en.ts` for English
2. Open `/src/i18n/locales/sk.ts` for Slovak
3. Add your translation keys in the same structure

Example:

```typescript
// en.ts
export default {
    products: {
        title: 'Products',
        add: 'Add Product',
        delete: 'Delete Product',
    },
}

// sk.ts
export default {
    products: {
        title: 'Produkty',
        add: 'Pridať produkt',
        delete: 'Vymazať produkt',
    },
}
```

## Adding New Languages

1. Create a new file in `/src/i18n/locales/` (e.g., `de.ts`)
2. Import it in `/src/i18n/index.ts`:
    ```typescript
    import de from './locales/de'
    ```
3. Add it to the messages object:
    ```typescript
    messages: {
      en,
      sk,
      de,
    }
    ```
4. Add the language to the store in `/src/stores/language.ts`:
    ```typescript
    { code: 'de', name: 'Deutsch', flag: '🇩🇪' }
    ```

## Translation with Parameters

```vue
<template>
    <p>{{ t('greeting', { name: userName }) }}</p>
</template>
```

In your locale file:

```typescript
{
    greeting: 'Hello, {name}!'
}
```

## Pluralization

```vue
<template>
    <p>{{ t('items', itemCount) }}</p>
</template>
```

In your locale file:

```typescript
{
    items: 'no items | one item | {count} items'
}
```

## Current Implementation

- ✅ Language persists in localStorage
- ✅ LanguageSelector component syncs with i18n
- ✅ Reservations view uses translations
- ✅ English and Slovak translations available
- ✅ FullCalendar integrated with i18n locale system

## FullCalendar Locale Integration

FullCalendar has its own locale system that's separate from Vue I18n. The calendar is now configured to:

1. **Use the correct locale** based on your i18n language selection
2. **Translate button text** (Today, Month, Week, Day, List) using your i18n translations
3. **Format dates** according to the selected locale (day names, month names, etc.)

The Slovak locale is imported from `@fullcalendar/core/locales/sk` and automatically applied when you switch to Slovak. For other languages, you would import them similarly:

```typescript
import deLocale from '@fullcalendar/core/locales/de'
import frLocale from '@fullcalendar/core/locales/fr'
```

Available FullCalendar locales include: ar, bg, ca, cs, da, de, el, es, et, eu, fa, fi, fr, gl, he, hi, hr, hu, id, is, it, ja, ko, lt, lv, nb, nl, pl, pt, ro, ru, sk, sl, sr, sv, th, tr, uk, vi, zh-cn, zh-tw, and more.

## Next Steps

Update other components to use translations:

- NavBar navigation items
- Sidebar menu items
- Auth pages (Login, Register)
- Calendar modal buttons
- Other views (Dashboard, Queue, etc.)
