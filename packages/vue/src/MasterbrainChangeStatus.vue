<script setup lang="ts">
import type { AppliedChangeSet } from '@airalogy/masterbrain-client';

const props = withDefaults(defineProps<{
  applied: AppliedChangeSet;
  undoing?: boolean;
  changedLabel?: string;
  viewLabel?: string;
  undoLabel?: string;
  undoingLabel?: string;
}>(), {
  undoing: false,
  changedLabel: 'AI changes applied',
  viewLabel: 'View changes',
  undoLabel: 'Undo',
  undoingLabel: 'Undoing…',
});

defineEmits<{
  view: [];
  undo: [];
}>();
</script>

<template>
  <div class="masterbrain-change-status" role="status">
    <span class="masterbrain-change-status__dot" aria-hidden="true" />
    <span class="masterbrain-change-status__text">
      {{ props.changedLabel }} · {{ props.applied.response.changed_files.length }}
    </span>
    <button type="button" class="masterbrain-change-status__button" @click="$emit('view')">
      {{ props.viewLabel }}
    </button>
    <button
      type="button"
      class="masterbrain-change-status__button masterbrain-change-status__button--primary"
      :disabled="props.undoing"
      @click="$emit('undo')"
    >
      {{ props.undoing ? props.undoingLabel : props.undoLabel }}
    </button>
  </div>
</template>

<style scoped>
.masterbrain-change-status { display: flex; align-items: center; gap: .5rem; padding: .625rem .75rem; border: 1px solid var(--masterbrain-safe-border, #a7f3d0); border-radius: .75rem; background: var(--masterbrain-safe-surface, #ecfdf5); color: var(--masterbrain-safe-strong, #065f46); font: 500 .875rem/1.25rem system-ui, sans-serif; }
.masterbrain-change-status__dot { width: .5rem; height: .5rem; flex: 0 0 auto; border-radius: 999px; background: var(--masterbrain-safe-dot, #10b981); }
.masterbrain-change-status__text { min-width: 0; flex: 1; }
.masterbrain-change-status__button { border: 0; background: transparent; color: var(--masterbrain-safe-text, #047857); cursor: pointer; font: inherit; }
.masterbrain-change-status__button--primary { padding: .25rem .625rem; border-radius: .5rem; background: var(--masterbrain-safe-bg, #d1fae5); }
.masterbrain-change-status__button:disabled { cursor: wait; opacity: .6; }
</style>
