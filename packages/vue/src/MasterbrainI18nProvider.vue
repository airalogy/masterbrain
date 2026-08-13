<script setup lang="ts">
import type { MasterbrainMessageOverrides } from './i18n.js';
import { toRef } from 'vue';
import { provideMasterbrainI18n } from './i18n.js';

const props = defineProps<{
  locale?: string | null;
  messages?: MasterbrainMessageOverrides | null;
}>();

const i18n = provideMasterbrainI18n({
  locale: toRef(props, 'locale'),
  messages: toRef(props, 'messages'),
});
</script>

<template>
  <slot :locale="i18n.locale.value" :messages="i18n.messages.value" :t="i18n.t" />
</template>
