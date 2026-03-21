<script setup lang="ts">
import avatarUrl from '../../assets/airalogy-chat.svg';

withDefaults(defineProps<{
  size?: 'sm' | 'md' | 'lg';
}>(), {
  size: 'md',
});
</script>

<template>
  <span :class="['ai-avatar', `ai-avatar--${size}`]">
    <img :src="avatarUrl" alt="Aira avatar" class="ai-avatar__image" />
  </span>
</template>

<style scoped>
.ai-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.16) 0%, rgba(14, 165, 233, 0.14) 100%);
  box-shadow: 0 18px 32px -24px rgba(37, 99, 235, 0.45);
}

.ai-avatar--sm {
  width: 34px;
  height: 34px;
  padding: 4px;
}

.ai-avatar--md {
  width: 42px;
  height: 42px;
  padding: 5px;
}

.ai-avatar--lg {
  width: 58px;
  height: 58px;
  padding: 6px;
}

.ai-avatar__image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 999px;
}
</style>
