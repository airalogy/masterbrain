<script setup lang="ts">
import type { CodeEditChangedFile, CodeEditResponse } from '@airalogy/masterbrain-client';
import type { MasterbrainMessageOverrides } from './i18n.js';
import { computed, toRef } from 'vue';
import { useMasterbrainI18n } from './i18n.js';

const props = withDefaults(defineProps<{
  result: CodeEditResponse;
  applying?: boolean;
  showApply?: boolean;
  showHeader?: boolean;
  showFooter?: boolean;
  locale?: string | null;
  messages?: MasterbrainMessageOverrides | null;
  title?: string;
  ariaLabel?: string;
  summaryLabel?: string;
  detailsLabel?: string;
  closeLabel?: string;
  applyLabel?: string;
  applyingLabel?: string;
  safeHint?: string;
  reviewHint?: string;
  fileCountLabel?: string;
  safeLabel?: string;
  warningLabel?: string;
  destructiveLabel?: string;
  createdLabel?: string;
  modifiedLabel?: string;
  deletedLabel?: string;
}>(), {
  applying: false,
  showApply: true,
  showHeader: true,
  showFooter: true,
});

const i18n = useMasterbrainI18n({
  locale: toRef(props, 'locale'),
  messages: toRef(props, 'messages'),
});
const labels = computed(() => {
  const title = props.title ?? i18n.t('changeReview.title');
  return {
    title,
    ariaLabel: props.ariaLabel ?? title,
    summary: props.summaryLabel ?? i18n.t('changeReview.summary'),
    details: props.detailsLabel ?? i18n.t('changeReview.technicalDiff'),
    close: props.closeLabel ?? i18n.t('changeReview.close'),
    apply: props.applyLabel ?? i18n.t('changeReview.applyChanges'),
    applying: props.applyingLabel ?? i18n.t('changeReview.applying'),
    safeHint: props.safeHint ?? i18n.t('changeReview.safeHint'),
    reviewHint: props.reviewHint ?? i18n.t('changeReview.reviewHint'),
    safe: props.safeLabel ?? i18n.t('changeReview.safe'),
    warning: props.warningLabel ?? i18n.t('changeReview.warning'),
    destructive: props.destructiveLabel ?? i18n.t('changeReview.destructive'),
    created: props.createdLabel ?? i18n.t('changeReview.created'),
    modified: props.modifiedLabel ?? i18n.t('changeReview.modified'),
    deleted: props.deletedLabel ?? i18n.t('changeReview.deleted'),
  };
});

defineEmits<{
  close: [];
  apply: [];
}>();

function statusLabel(change: CodeEditChangedFile) {
  if (change.status === 'created') return labels.value.created;
  if (change.status === 'modified') return labels.value.modified;
  return labels.value.deleted;
}

function riskLabel() {
  if (props.result.risk.level === 'safe') return labels.value.safe;
  if (props.result.risk.level === 'warning') return labels.value.warning;
  return labels.value.destructive;
}

function fileCountText() {
  return props.fileCountLabel
    ? `${props.result.changed_files.length} ${props.fileCountLabel}`
    : i18n.t('changeReview.fileCount', { count: props.result.changed_files.length });
}
</script>

<template>
  <section class="masterbrain-change-review" :aria-label="labels.ariaLabel">
    <slot name="header" :risk-label="riskLabel()">
      <header v-if="props.showHeader" class="masterbrain-change-review__header">
        <div>
          <h2 class="masterbrain-change-review__title">{{ labels.title }}</h2>
          <p class="masterbrain-change-review__hint">
            {{ props.result.risk.level === 'safe' ? labels.safeHint : labels.reviewHint }}
          </p>
        </div>
        <span :class="['masterbrain-change-review__risk', `masterbrain-change-review__risk--${props.result.risk.level}`]">
          {{ riskLabel() }}
        </span>
      </header>
    </slot>

    <slot name="summary">
      <div class="masterbrain-change-review__summary">
        <strong>{{ labels.summary }}</strong>
        <span>{{ fileCountText() }}</span>
        <p>{{ props.result.message }}</p>
      </div>
    </slot>

    <slot name="warnings" :reasons="props.result.risk.reasons">
      <ul v-if="props.result.risk.reasons.length" class="masterbrain-change-review__warnings">
        <li v-for="reason in props.result.risk.reasons" :key="reason">{{ reason }}</li>
      </ul>
    </slot>

    <article v-for="change in props.result.changed_files" :key="change.path" class="masterbrain-change-review__file">
      <slot name="file-header" :change="change" :status-label="statusLabel(change)">
        <header class="masterbrain-change-review__file-header">
          <span class="masterbrain-change-review__status">{{ statusLabel(change) }}</span>
          <strong>{{ change.name }}</strong>
          <code>{{ change.path }}</code>
        </header>
      </slot>
      <slot name="diff" :change="change">
        <details>
          <summary>{{ labels.details }}</summary>
          <pre class="masterbrain-change-review__diff">{{ change.diff }}</pre>
        </details>
      </slot>
    </article>

    <slot name="footer">
      <footer v-if="props.showFooter" class="masterbrain-change-review__footer">
        <button type="button" class="masterbrain-change-review__button" @click="$emit('close')">{{ labels.close }}</button>
        <button
          v-if="props.showApply && props.result.risk.recommended_action !== 'block'"
          type="button"
          class="masterbrain-change-review__button masterbrain-change-review__button--primary"
          :disabled="props.applying"
          @click="$emit('apply')"
        >
          {{ props.applying ? labels.applying : labels.apply }}
        </button>
      </footer>
    </slot>
  </section>
</template>

<style scoped>
.masterbrain-change-review { display: grid; gap: 1rem; color: var(--masterbrain-text, #1f2937); font: 400 .875rem/1.5 system-ui, sans-serif; }
.masterbrain-change-review__header, .masterbrain-change-review__file-header, .masterbrain-change-review__footer { display: flex; align-items: center; gap: .75rem; }
.masterbrain-change-review__header { align-items: flex-start; justify-content: space-between; }
.masterbrain-change-review__title { margin: 0; font-size: 1.125rem; }
.masterbrain-change-review__hint { margin: .25rem 0 0; color: var(--masterbrain-muted, #6b7280); }
.masterbrain-change-review__risk, .masterbrain-change-review__status { border-radius: 999px; padding: .125rem .5rem; background: var(--masterbrain-badge-bg, #e5e7eb); font-size: .75rem; text-transform: capitalize; }
.masterbrain-change-review__risk--safe { background: var(--masterbrain-safe-bg, #d1fae5); color: var(--masterbrain-safe-text, #047857); }
.masterbrain-change-review__risk--warning { background: var(--masterbrain-warning-bg, #fef3c7); color: var(--masterbrain-warning-text, #92400e); }
.masterbrain-change-review__risk--destructive { background: var(--masterbrain-danger-bg, #fee2e2); color: var(--masterbrain-danger-text, #b91c1c); }
.masterbrain-change-review__summary { display: grid; grid-template-columns: 1fr auto; gap: .25rem 1rem; border: 1px solid var(--masterbrain-accent-border, #bfdbfe); border-radius: .75rem; background: var(--masterbrain-accent-bg, #eff6ff); padding: .75rem; color: var(--masterbrain-accent-text, #1e40af); }
.masterbrain-change-review__summary p { grid-column: 1 / -1; margin: .25rem 0 0; white-space: pre-wrap; }
.masterbrain-change-review__warnings { margin: 0; border-radius: .75rem; background: var(--masterbrain-warning-surface, #fffbeb); padding: .75rem .75rem .75rem 2rem; color: var(--masterbrain-warning-text, #92400e); }
.masterbrain-change-review__file { overflow: hidden; border: 1px solid var(--masterbrain-border, #e5e7eb); border-radius: .75rem; }
.masterbrain-change-review__file-header { padding: .75rem; }
.masterbrain-change-review__file-header code { min-width: 0; margin-left: auto; overflow: hidden; color: var(--masterbrain-muted, #6b7280); text-overflow: ellipsis; white-space: nowrap; }
.masterbrain-change-review__file details { border-top: 1px solid var(--masterbrain-border, #e5e7eb); padding: .75rem; }
.masterbrain-change-review__diff { max-height: 22rem; overflow: auto; margin: .75rem 0 0; border-radius: .5rem; background: #111827; padding: .75rem; color: #e5e7eb; font: 400 .75rem/1.5 ui-monospace, monospace; white-space: pre; }
.masterbrain-change-review__footer { justify-content: flex-end; }
.masterbrain-change-review__button { border: 1px solid var(--masterbrain-button-border, #d1d5db); border-radius: .5rem; background: var(--masterbrain-button-bg, white); padding: .5rem .75rem; color: var(--masterbrain-text, #1f2937); cursor: pointer; }
.masterbrain-change-review__button--primary { border-color: var(--masterbrain-primary, #2563eb); background: var(--masterbrain-primary, #2563eb); color: var(--masterbrain-primary-text, white); }
.masterbrain-change-review__button:disabled { cursor: wait; opacity: .6; }
</style>
