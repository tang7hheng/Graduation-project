<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue'
import { renderMarkdownTo } from '@/composables/useMarkdown'
import type { MessageOut } from '@/api/client'

const props = defineProps<{
  message: MessageOut
  streaming?: boolean
  productCards?: any[]
}>()

const contentEl = ref<HTMLElement>()

function update() {
  if (!contentEl.value) return
  renderMarkdownTo(contentEl.value, props.message.content, !props.streaming)
}

onMounted(update)
watch(() => props.message.content, () => nextTick(update))
</script>

<template>
  <div class="bubble-row" :class="message.role">
    <div class="avatar">{{ message.role === 'user' ? '我' : 'AI' }}</div>
    <div class="bubble-content">
      <div
        ref="contentEl"
        class="markdown-body"
        :class="{ 'streaming-caret': streaming }"
      ></div>
    </div>
  </div>
</template>

<style scoped>
.bubble-row {
  display: flex;
  gap: 12px;
  margin: 16px 0;
  align-items: flex-start;
  animation: slide-in 0.3s ease-out;
}
.bubble-row.user {
  flex-direction: row-reverse;
}
.avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  background: var(--accent-primary);
  box-shadow: 0 2px 6px rgba(79, 70, 229, 0.2);
}
.bubble-row.user .avatar {
  background: #64748b;
  box-shadow: 0 2px 6px rgba(100, 116, 139, 0.15);
}
.bubble-content {
  max-width: 72%;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-base);
  border-top-left-radius: 4px;
}
.bubble-row.user .bubble-content {
  background: var(--accent-primary-light);
  border-color: #c7d2fe;
  border-top-left-radius: var(--radius-md);
  border-top-right-radius: 4px;
}
</style>
