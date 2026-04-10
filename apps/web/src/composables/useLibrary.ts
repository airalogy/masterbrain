import { computed, ref, shallowRef } from 'vue';
import type {
  LibraryImportResponse,
  LibraryImportResult,
  LibraryProtocolPreview,
  LibraryRecordDetail,
  LibraryState,
} from '../types/index.ts';

const EMPTY_LIBRARY_STATE: LibraryState = {
  db_path: '',
  archive_count: 0,
  protocol_count: 0,
  record_count: 0,
  archives: [],
  protocols: [],
  records: [],
};

async function readApiError(res: Response): Promise<string> {
  const fallback = `Library API error ${res.status}`;
  try {
    const text = await res.text();
    if (!text.trim()) return fallback;
    try {
      const parsed = JSON.parse(text) as { detail?: string };
      return parsed.detail ? `${fallback}: ${parsed.detail}` : `${fallback}: ${text}`;
    } catch {
      return `${fallback}: ${text}`;
    }
  } catch {
    return fallback;
  }
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    throw new Error(await readApiError(res));
  }
  return res.json() as Promise<T>;
}

export function useLibrary() {
  const libraryState = shallowRef<LibraryState>({ ...EMPTY_LIBRARY_STATE });
  const isLoadingLibrary = ref(true);
  const isLoadingPreview = ref(false);
  const libraryError = ref<string | null>(null);
  const lastImportResult = shallowRef<LibraryImportResult | null>(null);
  const selectedProtocolPreview = shallowRef<LibraryProtocolPreview | null>(null);
  const selectedRecordDetail = shallowRef<LibraryRecordDetail | null>(null);
  const selectedProtocolId = ref<number | null>(null);
  const selectedRecordId = ref<number | null>(null);

  const hasLibrary = computed(() => libraryState.value.archive_count > 0);

  function applyLibraryState(state: LibraryState) {
    libraryState.value = state;

    if (
      selectedProtocolId.value !== null &&
      !state.protocols.some(protocol => protocol.id === selectedProtocolId.value)
    ) {
      selectedProtocolId.value = null;
      selectedProtocolPreview.value = null;
    }

    if (
      selectedRecordId.value !== null &&
      !state.records.some(record => record.id === selectedRecordId.value)
    ) {
      selectedRecordId.value = null;
      selectedRecordDetail.value = null;
    }
  }

  async function refreshLibrary() {
    isLoadingLibrary.value = true;
    try {
      const state = await requestJson<LibraryState>('/api/endpoints/library');
      applyLibraryState(state);
      libraryError.value = null;
    } catch (error) {
      libraryError.value = error instanceof Error ? error.message : 'Failed to load local library.';
    } finally {
      isLoadingLibrary.value = false;
    }
  }

  async function importAiraPath(path: string) {
    try {
      const response = await requestJson<LibraryImportResponse>('/api/endpoints/library/import-path', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      });
      lastImportResult.value = response.result;
      applyLibraryState(response.state);
      libraryError.value = null;
      return response.result;
    } catch (error) {
      libraryError.value = error instanceof Error ? error.message : 'Failed to import archive path.';
      throw error;
    }
  }

  async function importAiraFile(file: File) {
    const params = new URLSearchParams({ source_name: file.name });
    try {
      const response = await requestJson<LibraryImportResponse>(
        `/api/endpoints/library/import-aira?${params.toString()}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/octet-stream' },
          body: file,
        },
      );
      lastImportResult.value = response.result;
      applyLibraryState(response.state);
      libraryError.value = null;
      return response.result;
    } catch (error) {
      libraryError.value = error instanceof Error ? error.message : 'Failed to upload archive.';
      throw error;
    }
  }

  async function previewProtocol(protocolId: number) {
    isLoadingPreview.value = true;
    try {
      const preview = await requestJson<LibraryProtocolPreview>(
        `/api/endpoints/library/protocol/${protocolId}/preview`,
      );
      selectedProtocolId.value = protocolId;
      selectedProtocolPreview.value = preview;
      selectedRecordId.value = null;
      selectedRecordDetail.value = null;
      libraryError.value = null;
      return preview;
    } catch (error) {
      libraryError.value = error instanceof Error ? error.message : 'Failed to preview protocol.';
      throw error;
    } finally {
      isLoadingPreview.value = false;
    }
  }

  async function previewRecord(recordId: number) {
    isLoadingPreview.value = true;
    try {
      const detail = await requestJson<LibraryRecordDetail>(
        `/api/endpoints/library/record/${recordId}`,
      );
      selectedRecordId.value = recordId;
      selectedRecordDetail.value = detail;
      selectedProtocolId.value = null;
      selectedProtocolPreview.value = null;
      libraryError.value = null;
      return detail;
    } catch (error) {
      libraryError.value = error instanceof Error ? error.message : 'Failed to load record JSON.';
      throw error;
    } finally {
      isLoadingPreview.value = false;
    }
  }

  async function loadProtocolToWorkspace(protocolId: number) {
    try {
      const state = await requestJson<LibraryState>(
        `/api/endpoints/library/protocol/${protocolId}/load-workspace`,
        {
          method: 'POST',
        },
      );
      applyLibraryState(state);
      libraryError.value = null;
      return true;
    } catch (error) {
      libraryError.value = error instanceof Error ? error.message : 'Failed to load protocol into workspace.';
      return false;
    }
  }

  void refreshLibrary();

  return {
    libraryState,
    hasLibrary,
    isLoadingLibrary,
    isLoadingPreview,
    libraryError,
    lastImportResult,
    selectedProtocolPreview,
    selectedRecordDetail,
    selectedProtocolId,
    selectedRecordId,
    refreshLibrary,
    importAiraPath,
    importAiraFile,
    previewProtocol,
    previewRecord,
    loadProtocolToWorkspace,
  };
}
