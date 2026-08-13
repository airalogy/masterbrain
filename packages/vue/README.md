# @airalogy/masterbrain-vue

Vue state and presentation primitives for Masterbrain Protocol editing.

- `useCodeEditAssistant` owns safe auto-apply, review, conflict detection, and undo state.
- `MasterbrainChangeReview` and `MasterbrainChangeStatus` provide host-neutral UI.
- Built-in `en-US` and `zh-CN` messages keep shared UI localized without copying labels into every host.
- `@airalogy/masterbrain-vue/monaco` exports an optional Monaco Diff viewer. Install and configure `monaco-editor` in the host only when that view is used.

Platform remains responsible for authentication, billing, audit, routing, its product-specific messages and modal shells, and adapting its editor store to the shared `WorkspaceAdapter` contract. Masterbrain owns localization for the UI it ships.

Visual tokens use `--masterbrain-*` CSS custom properties with accessible defaults, so product themes do not require forking the components.
`MasterbrainChangeReview` also exposes header, summary, warnings, file-header, diff, and footer slots; product hosts can keep their own modal and design system without duplicating change-set behavior.

Import the default component styles once in the host entry point:

```ts
import '@airalogy/masterbrain-vue/style.css';
```

```ts
import { useCodeEditAssistant } from '@airalogy/masterbrain-vue';

const assistant = useCodeEditAssistant({
  client,
  workspace,
  // Safe edits auto-apply by default. Set false for a strict-review host.
  autoApply: true,
});

const result = await assistant.submit(request);
```

Configure localization once for an application. Locale refs are reactive, common variants such as `zh_CN` are normalized, and unsupported locales fall back to English:

```ts
import { createApp, ref } from 'vue';
import { createMasterbrainI18n } from '@airalogy/masterbrain-vue';

const locale = ref('zh-CN');
createApp(App)
  .use(createMasterbrainI18n({ locale }))
  .mount('#app');
```

For a subtree, use the provider instead:

```vue
<script setup lang="ts">
import { MasterbrainI18nProvider } from '@airalogy/masterbrain-vue';
</script>

<template>
  <MasterbrainI18nProvider :locale="currentLocale">
    <MasterbrainChangeReview :result="result" />
  </MasterbrainI18nProvider>
</template>
```

Both the provider and individual components accept a locale-keyed `messages` catalog for product-specific wording. Existing `*Label` props remain supported as the highest-priority one-off override.

Import Monaco only in hosts that render a visual diff:

```ts
import { MasterbrainMonacoDiff } from '@airalogy/masterbrain-vue/monaco';
```
