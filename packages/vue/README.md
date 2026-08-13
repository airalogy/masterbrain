# @airalogy/masterbrain-vue

Vue state and presentation primitives for Masterbrain Protocol editing.

- `useCodeEditAssistant` owns safe auto-apply, review, conflict detection, and undo state.
- `MasterbrainChangeReview` and `MasterbrainChangeStatus` provide host-neutral UI.
- `@airalogy/masterbrain-vue/monaco` exports an optional Monaco Diff viewer. Install and configure `monaco-editor` in the host only when that view is used.

Platform remains responsible for authentication, billing, audit, routing, localization, modal shells, and adapting its editor store to the shared `WorkspaceAdapter` contract.

All user-facing labels on the review/status primitives can be supplied by the host. Visual tokens use `--masterbrain-*` CSS custom properties with accessible defaults, so product themes do not require forking the components.
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

Import Monaco only in hosts that render a visual diff:

```ts
import { MasterbrainMonacoDiff } from '@airalogy/masterbrain-vue/monaco';
```
