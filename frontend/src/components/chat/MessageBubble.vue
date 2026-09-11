<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue'
import { renderMarkdownTo } from '@/composables/useMarkdown'
import type { MessageOut } from '@/api/client'
import ProductCards from './ProductCards.vue'

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
    <div class="avatar">{{ message.role === 'user' ? '我' : '客服' }}</div>
    <div class="bubble-content">
      <div
        ref="contentEl"
        class="markdown-body"
        :class="{ 'streaming-caret': streaming }"
      ></div>
      <ProductCards
        v-if="message.product_cards_json && message.product_cards_json.length"
        :cards="message.product_cards_json"
      />
    </div>
  </div>
</template>

<style scoped>
.bubble-row {
  display: flex;
  gap: 12px;
  margin: 16px 0;
  align-items: flex-start;
}
.bubble-row.user {
  flex-direction: row-reverse;
}
.avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #fff;
  background: #3b82f6;
}
.bubble-row.user .avatar {
  background: #10b981;
}
.bubble-content {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}
.bubble-row.user .bubble-content {
  background: #dbeafe;
  border-color: #bfdbfe;
}
</style>
