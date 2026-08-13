import {
  applyCodeEditResponse,
  handleCodeEditResponse,
  undoAppliedChangeSet,
  type AppliedChangeSet,
  type CodeEditApplicationResult,
  type CodeEditRequest,
  type CodeEditResponse,
  type MasterbrainClient,
  type WorkspaceAdapter,
} from '@airalogy/masterbrain-client';
import { computed, ref, shallowRef } from 'vue';

export interface CodeEditClient {
  runCodeEdit(request: CodeEditRequest, options?: { signal?: AbortSignal }): Promise<CodeEditResponse>;
}

export interface UseCodeEditAssistantOptions {
  client: CodeEditClient | MasterbrainClient;
  workspace: WorkspaceAdapter;
  /** Safe changes apply immediately by default. Set false for stricter hosts. */
  autoApply?: boolean;
}

export function useCodeEditAssistant(options: UseCodeEditAssistantOptions) {
  const loading = ref(false);
  const applying = ref(false);
  const undoing = ref(false);
  const error = shallowRef<Error | null>(null);
  const latestResponse = shallowRef<CodeEditResponse | null>(null);
  const pendingReview = shallowRef<CodeEditResponse | null>(null);
  const latestApplied = shallowRef<AppliedChangeSet | null>(null);
  const status = computed(() => {
    if (loading.value) return 'loading' as const;
    if (applying.value) return 'applying' as const;
    if (undoing.value) return 'undoing' as const;
    if (pendingReview.value) return 'review' as const;
    if (latestApplied.value) return 'applied' as const;
    if (latestResponse.value?.outcome === 'answer') return 'answer' as const;
    if (error.value) return 'error' as const;
    return 'idle' as const;
  });

  async function submit(
    request: CodeEditRequest,
    submitOptions: { signal?: AbortSignal } = {},
  ): Promise<CodeEditApplicationResult> {
    loading.value = true;
    error.value = null;
    pendingReview.value = null;
    try {
      const response = await options.client.runCodeEdit(request, submitOptions);
      latestResponse.value = response;
      let result: CodeEditApplicationResult;
      if (options.autoApply === false && response.outcome === 'changed') {
        result = response.risk.recommended_action === 'block'
          ? { status: 'blocked', response }
          : { status: 'review', response };
      } else {
        result = await handleCodeEditResponse(response, options.workspace);
      }
      if (result.status === 'review') pendingReview.value = response;
      if (result.status === 'applied') latestApplied.value = result.applied;
      return result;
    } catch (caught) {
      error.value = caught instanceof Error ? caught : new Error(String(caught));
      throw caught;
    } finally {
      loading.value = false;
    }
  }

  async function applyPending(): Promise<AppliedChangeSet | null> {
    const response = pendingReview.value;
    if (!response) return null;
    applying.value = true;
    error.value = null;
    try {
      const applied = await applyCodeEditResponse(response, options.workspace);
      latestApplied.value = applied;
      pendingReview.value = null;
      return applied;
    } catch (caught) {
      error.value = caught instanceof Error ? caught : new Error(String(caught));
      throw caught;
    } finally {
      applying.value = false;
    }
  }

  async function undoLatest(): Promise<boolean> {
    const applied = latestApplied.value;
    if (!applied) return false;
    undoing.value = true;
    error.value = null;
    try {
      await undoAppliedChangeSet(applied, options.workspace);
      latestApplied.value = null;
      return true;
    } catch (caught) {
      error.value = caught instanceof Error ? caught : new Error(String(caught));
      throw caught;
    } finally {
      undoing.value = false;
    }
  }

  function dismissReview() {
    pendingReview.value = null;
  }

  function clear() {
    error.value = null;
    latestResponse.value = null;
    pendingReview.value = null;
    latestApplied.value = null;
  }

  return {
    loading,
    applying,
    undoing,
    error,
    status,
    latestResponse,
    pendingReview,
    latestApplied,
    submit,
    applyPending,
    undoLatest,
    dismissReview,
    clear,
  };
}
