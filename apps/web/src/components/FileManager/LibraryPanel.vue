<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type {
  LibraryImportResult,
  LibraryProtocolPreview,
  LibraryRecordDetail,
  LibraryState,
} from '../../types/index.ts';
import logoIconUrl from '../../assets/airalogy-logo.svg';

const props = defineProps<{
  libraryState: LibraryState;
  hasWorkspace: boolean;
  isLoadingLibrary: boolean;
  isLoadingPreview: boolean;
  libraryError: string | null;
  lastImportResult: LibraryImportResult | null;
  selectedProtocolPreview: LibraryProtocolPreview | null;
  selectedRecordDetail: LibraryRecordDetail | null;
}>();

const emit = defineEmits<{
  importFile: [file: File];
  importPath: [path: string];
  refreshLibrary: [];
  previewProtocol: [protocolId: number];
  previewRecord: [recordId: number];
  loadProtocol: [protocolId: number];
  collapse: [];
}>();

const archivePathInput = ref('');
const fileInputRef = ref<HTMLInputElement | null>(null);
const selectedPreviewPath = ref('');

watch(
  () => props.selectedProtocolPreview?.files,
  (files) => {
    selectedPreviewPath.value = files?.[0]?.path ?? '';
  },
  { immediate: true },
);

const selectedPreviewFile = computed(() => {
  const files = props.selectedProtocolPreview?.files ?? [];
  return files.find(file => file.path === selectedPreviewPath.value) ?? files[0] ?? null;
});

const importBanner = computed(() => {
  const result = props.lastImportResult;
  if (!result) return null;
  const action = result.duplicate ? 'Archive already existed' : 'Archive imported';
  return `${action}: ${result.source_name} (${result.kind})`;
});

function handleImportPath() {
  const path = archivePathInput.value.trim();
  if (!path) return;
  emit('importPath', path);
}

function handleUploadClick() {
  fileInputRef.value?.click();
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  target.value = '';
  emit('importFile', file);
}

function shortId(value: string | null | undefined) {
  if (!value) return 'Unspecified';
  if (value.length <= 42) return value;
  return `${value.slice(0, 18)}...${value.slice(-12)}`;
}
</script>

<template>
  <div class="library-shell">
    <div class="library-shell__header">
      <div>
        <div class="library-shell__brand">
          <span class="library-shell__brand-mark">
            <img :src="logoIconUrl" alt="Airalogy logo" class="library-shell__brand-image" />
          </span>
          <span class="library-shell__brand-copy">
            <span class="library-shell__brand-name">Airalogy</span>
            <span class="library-shell__brand-product">Masterbrain</span>
          </span>
        </div>
        <p class="library-shell__eyebrow">Local Archive Library</p>
        <h2 class="library-shell__title">Protocol Records</h2>
      </div>
      <button
        title="Collapse panel"
        class="library-shell__icon-button"
        @click="emit('collapse')"
      >‹</button>
    </div>

    <div class="library-shell__meta">
      <span>{{ props.libraryState.archive_count }} archives</span>
      <span>{{ props.libraryState.protocol_count }} protocols</span>
      <span>{{ props.libraryState.record_count }} records</span>
      <span>{{ props.hasWorkspace ? 'Workspace ready' : 'Choose a workspace to load protocols' }}</span>
    </div>

    <div class="library-shell__card">
      <p class="library-shell__card-label">Library Database</p>
      <p class="library-shell__mono">{{ props.libraryState.db_path || 'Loading…' }}</p>
      <p v-if="props.libraryError" class="library-shell__error">{{ props.libraryError }}</p>
      <input
        v-model="archivePathInput"
        class="library-shell__input"
        placeholder="/path/to/archive.aira"
        @keydown.enter.prevent="handleImportPath"
      />
      <div class="library-shell__actions">
        <button
          class="library-shell__primary-button"
          :disabled="!archivePathInput.trim()"
          @click="handleImportPath"
        >Import Path</button>
        <button
          class="library-shell__secondary-button"
          @click="handleUploadClick"
        >Upload .aira</button>
        <button
          class="library-shell__secondary-button"
          @click="emit('refreshLibrary')"
        >Refresh</button>
      </div>
      <p v-if="importBanner" class="library-shell__success">{{ importBanner }}</p>
      <p v-if="props.isLoadingLibrary" class="library-shell__hint">Loading local library…</p>
      <p v-else-if="props.libraryState.archive_count === 0" class="library-shell__hint">
        Import a `.aira` file to persist protocols and records inside Masterbrain's local library.
      </p>
    </div>

    <div class="library-shell__section">
      <div class="library-shell__section-header">
        <h3>Archives</h3>
        <span>{{ props.libraryState.archives.length }}</span>
      </div>
      <div class="library-shell__list">
        <button
          v-for="archive in props.libraryState.archives"
          :key="archive.id"
          type="button"
          class="library-shell__list-item"
        >
          <span class="library-shell__list-title">{{ archive.source_name }}</span>
          <span class="library-shell__list-meta">{{ archive.kind }} · {{ archive.protocol_count }} protocols · {{ archive.record_count }} records</span>
          <span class="library-shell__list-code">{{ shortId(archive.source_path ?? archive.sha256) }}</span>
        </button>
      </div>
    </div>

    <div class="library-shell__section">
      <div class="library-shell__section-header">
        <h3>Protocols</h3>
        <span>{{ props.libraryState.protocols.length }}</span>
      </div>
      <div class="library-shell__list">
        <div
          v-for="protocol in props.libraryState.protocols"
          :key="protocol.id"
          class="library-shell__list-item library-shell__list-item--stacked"
        >
          <div>
            <span class="library-shell__list-title">{{ protocol.protocol_name }}</span>
            <span class="library-shell__list-meta">{{ shortId(protocol.protocol_id) }} · v{{ protocol.protocol_version ?? 'unversioned' }}</span>
            <span class="library-shell__list-code">{{ protocol.file_count }} files · {{ protocol.entrypoint }}</span>
          </div>
          <div class="library-shell__inline-actions">
            <button
              class="library-shell__secondary-button"
              @click="emit('previewProtocol', protocol.id)"
            >Preview</button>
            <button
              class="library-shell__primary-button"
              :disabled="!props.hasWorkspace"
              @click="emit('loadProtocol', protocol.id)"
            >Load to Workspace</button>
          </div>
        </div>
      </div>
    </div>

    <div class="library-shell__section">
      <div class="library-shell__section-header">
        <h3>Records</h3>
        <span>{{ props.libraryState.records.length }}</span>
      </div>
      <div class="library-shell__list">
        <div
          v-for="record in props.libraryState.records"
          :key="record.id"
          class="library-shell__list-item library-shell__list-item--stacked"
        >
          <div>
            <span class="library-shell__list-title">{{ record.record_id || `Record #${record.id}` }}</span>
            <span class="library-shell__list-meta">{{ shortId(record.protocol_id) }} · v{{ record.record_version ?? 'unknown' }}</span>
            <span class="library-shell__list-code">{{ record.source_path || 'inline record' }} · item {{ record.source_index }}</span>
          </div>
          <div class="library-shell__inline-actions">
            <button
              class="library-shell__secondary-button"
              @click="emit('previewRecord', record.id)"
            >Preview JSON</button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="props.selectedProtocolPreview || props.selectedRecordDetail"
      class="library-shell__detail"
    >
      <div class="library-shell__section-header">
        <h3>Detail</h3>
        <span v-if="props.isLoadingPreview">Loading…</span>
      </div>

      <template v-if="props.selectedProtocolPreview">
        <p class="library-shell__detail-title">{{ props.selectedProtocolPreview.protocol.protocol_name }}</p>
        <p class="library-shell__detail-meta">
          {{ props.selectedProtocolPreview.total_file_count }} files · {{ props.selectedProtocolPreview.binary_file_count }} binary skipped in preview
        </p>
        <div class="library-shell__file-tabs">
          <button
            v-for="file in props.selectedProtocolPreview.files"
            :key="file.path"
            type="button"
            :class="['library-shell__file-tab', selectedPreviewFile?.path === file.path ? 'library-shell__file-tab--active' : '']"
            @click="selectedPreviewPath = file.path"
          >{{ file.path }}</button>
        </div>
        <pre v-if="selectedPreviewFile" class="library-shell__code">{{ selectedPreviewFile.content }}</pre>
      </template>

      <template v-else-if="props.selectedRecordDetail">
        <p class="library-shell__detail-title">{{ props.selectedRecordDetail.record.record_id || `Record #${props.selectedRecordDetail.record.id}` }}</p>
        <p class="library-shell__detail-meta">
          {{ shortId(props.selectedRecordDetail.record.protocol_id) }} · source {{ props.selectedRecordDetail.record.source_path || 'inline' }}
        </p>
        <pre class="library-shell__code">{{ JSON.stringify(props.selectedRecordDetail.payload, null, 2) }}</pre>
      </template>
    </div>

    <input
      ref="fileInputRef"
      type="file"
      accept=".aira"
      class="hidden"
      @change="handleFileChange"
    />
  </div>
</template>

<style scoped>
.library-shell {
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  min-height: 0;
  background: transparent;
  color: var(--text-primary);
  overflow: hidden;
}

.library-shell__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 18px 14px;
  border-bottom: 1px solid var(--border-color);
}

.library-shell__brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.library-shell__brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: var(--panel-muted);
  border: 1px solid var(--border-color);
}

.library-shell__brand-image {
  width: 24px;
  height: 24px;
}

.library-shell__brand-copy {
  display: flex;
  flex-direction: column;
}

.library-shell__brand-name,
.library-shell__brand-product,
.library-shell__eyebrow,
.library-shell__list-meta,
.library-shell__list-code,
.library-shell__detail-meta,
.library-shell__hint,
.library-shell__mono,
.library-shell__success,
.library-shell__error {
  font-size: 12px;
  line-height: 1.5;
}

.library-shell__brand-name {
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.library-shell__brand-product {
  font-size: 14px;
  font-weight: 700;
}

.library-shell__eyebrow {
  margin: 0 0 4px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.library-shell__title {
  margin: 0;
  font-size: 24px;
  line-height: 1.1;
}

.library-shell__icon-button {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 999px;
  background: var(--panel-subtle);
  color: var(--text-secondary);
  cursor: pointer;
}

.library-shell__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 12px;
}

.library-shell__card,
.library-shell__section,
.library-shell__detail {
  margin: 14px 14px 0;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: var(--panel-solid);
  box-shadow: var(--shadow-md);
}

.library-shell__card-label,
.library-shell__detail-title,
.library-shell__section-header h3,
.library-shell__list-title {
  margin: 0;
  font-weight: 700;
  color: var(--text-primary);
}

.library-shell__mono,
.library-shell__list-code {
  font-family: "IBM Plex Mono", "SFMono-Regular", ui-monospace, Menlo, Monaco, Consolas, monospace;
  word-break: break-all;
}

.library-shell__input {
  width: 100%;
  margin-top: 10px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--panel-muted);
  color: var(--text-primary);
  padding: 10px 12px;
}

.library-shell__actions,
.library-shell__inline-actions,
.library-shell__section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.library-shell__actions,
.library-shell__inline-actions {
  margin-top: 10px;
}

.library-shell__primary-button,
.library-shell__secondary-button {
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 8px 10px;
  cursor: pointer;
}

.library-shell__primary-button {
  background: var(--accent);
  color: #fff;
}

.library-shell__secondary-button {
  background: var(--panel-subtle);
  color: var(--text-secondary);
  border-color: var(--border-color);
}

.library-shell__primary-button:disabled,
.library-shell__secondary-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.library-shell__hint,
.library-shell__success,
.library-shell__error {
  margin: 10px 0 0;
}

.library-shell__success {
  color: var(--success);
}

.library-shell__error {
  color: var(--danger);
}

.library-shell__section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.library-shell__section-header span {
  color: var(--text-muted);
  font-size: 12px;
}

.library-shell__list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 180px;
  overflow: auto;
}

.library-shell__list-item {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 4px;
  border: 1px solid var(--border-color);
  border-radius: 14px;
  background: var(--panel-muted);
  padding: 10px 12px;
  text-align: left;
  color: inherit;
}

.library-shell__list-item--stacked {
  gap: 10px;
}

.library-shell__list-meta,
.library-shell__detail-meta {
  color: var(--text-muted);
}

.library-shell__detail {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
  overflow: hidden;
}

.library-shell__file-tabs {
  display: flex;
  gap: 6px;
  overflow: auto;
}

.library-shell__file-tab {
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: var(--panel-muted);
  color: var(--text-secondary);
  padding: 6px 10px;
  white-space: nowrap;
  cursor: pointer;
}

.library-shell__file-tab--active {
  border-color: var(--accent-border);
  background: var(--accent-soft);
  color: var(--accent);
}

.library-shell__code {
  margin: 0;
  padding: 12px;
  border: 1px solid var(--code-border);
  border-radius: 14px;
  background: var(--code-bg);
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.6;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
