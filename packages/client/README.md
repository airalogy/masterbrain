# @airalogy/masterbrain-client

Framework-neutral types, HTTP transport, and conflict-safe workspace change helpers for Masterbrain.

The browser client never stores model-provider credentials. Use a same-origin Platform proxy in hosted products, or point the fetch transport at a locally trusted Masterbrain service.

The Python Pydantic models remain the source of truth for the public request/response schema. The generated fixture is exported as `@airalogy/masterbrain-client/schema/code-edit.v1.json`; CI rejects drift between that fixture and the backend models.

```ts
import {
  MasterbrainClient,
  createFetchTransport,
  handleCodeEditResponse,
} from '@airalogy/masterbrain-client';

const client = new MasterbrainClient(createFetchTransport({
  // Hosted products should inject their own same-origin authentication here.
  headers: () => ({ Authorization: `Bearer ${sessionToken}` }),
}));

const response = await client.runCodeEdit({
  model: { name: 'qwen3.5-flash', enable_thinking: false },
  prompt: 'Add an optional operator_notes field.',
  files: await workspace.listFiles(),
});

const application = await handleCodeEditResponse(response, workspace);
// application.status is answer, applied, review, or blocked.
```

The host-provided `WorkspaceAdapter` receives one mutation batch for each apply or undo. It should persist that batch transactionally where the storage layer supports transactions.
