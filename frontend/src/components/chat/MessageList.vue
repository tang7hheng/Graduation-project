<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import MessageBubble from './MessageBubble.vue'
import ProductCards from './ProductCards.vue'
import SourceCitations from './SourceCitations.vue'
import type { MessageOut } from '@/api/client'

const props = defineProps<{
  messages: MessageOut[]
  streamingText: string
  isStreaming: boolean
  thinkingMessage?: string
  streamingProductCards?: any[]
  streamingSources?: any[]
}>()

const containerEl = ref<HTMLElement>()

function scrollToBottom() {
  nextTick(() => {
    if (containerEl.value) {
      containerEl.value.scrollTop = containerEl.value.scrollHeight
    }
  })
}

watch(() => props.messages.length, scrollToBottom)
watch(() => props.streamingText, scrollToBottom)
watch(() => props.streamingProductCards, scrollToBottom, { deep: true })
</script>

<template>
  <div ref="containerEl" class="message-list">
    <div v-if="messages.length === 0 && !streamingText" class="empty-hint">
      <div class="empty-icon">购</div>
      <p class="empty-title">智能导购客服</p>
      <p class="sub">告诉我您的需求,我会帮您找到最合适的商品</p>
    </div>
    <template v-for="(m, i) in messages" :key="m.id">
      <MessageBubble :message="m" />
      <ProductCards
        v-if="m.role === 'assistant' && m.product_cards_json?.length"
        :cards="m.product_cards_json"
      />
      <SourceCitations
        v-if="m.role === 'assistant' && m.sources_json?.length"
        :sources="m.sources_json"
      />
      <span v-if="i < messages.length - 1" class="gap"></span>
    </template>
    <!-- Thinking indicator -->
    <div v-if="isStreaming && thinkingMessage && !streamingText" class="thinking-row">
      <div class="avatar">AI</div>
      <div class="thinking-bubble">
        <div class="dots">
          <span></span><span></span><span></span>
        </div>
        <span class="thinking-text">{{ thinkingMessage }}</span>
      </div>
    </div>

    <!-- Streaming bubble -->
    <MessageBubble
      v-if="streamingText"
      :message="{
        id: -1,
        session_id: '',
        role: 'assistant',
        content: streamingText,
        sources_json: [],
        product_cards_json: [],
        created_at: new Date().toISOString(),
      }"
      :streaming="true"
    />
    <ProductCards
      v-if="isStreaming && streamingProductCards && streamingProductCards.length"
      :cards="streamingProductCards"
    />
  </div>
</template>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  max-width: 960px;
  margin: 0 auto;
  width: 100%;
}
.empty-hint {
  text-align: center;
  padding: 80px 24px;
  animation: fade-in 0.5s ease-out;
}
.empty-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: var(--accent-primary);
  color: #fff;
  font-weight: 800;
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
}
.empty-title {
  font-weight: 700;
  font-size: 18px;
  color: var(--text-primary);
  margin: 0 0 6px;
}
.empty-hint .sub {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: 0;
}
.gap { display: block; height: 4px; }

/* Thinking indicator */
.thinking-row {
  display: flex;
  gap: 12px;
  margin: 16px 0;
  align-items: flex-start;
  animation: slide-in 0.3s ease-out;
}
.thinking-row .avatar {
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
.thinking-bubble {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  border-top-left-radius: 4px;
  background: var(--bg-surface);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-base);
}
.thinking-bubble .dots { display: inline-flex; gap: 4px; }
.thinking-bubble .dots span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent-primary);
  animation: dot-bounce 1.4s ease-in-out infinite both;
}
.thinking-bubble .dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-bubble .dots span:nth-child(2) { animation-delay: -0.16s; }
.thinking-bubble .dots span:nth-child(3) { animation-delay: 0s; }
.thinking-text {
  font-size: 14px;
  color: var(--text-tertiary);
}
@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}
</style>
