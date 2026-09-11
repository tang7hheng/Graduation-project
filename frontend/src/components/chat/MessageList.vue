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
      <p>暂无消息。请输入您的问题开始对话。</p>
      <p class="sub">导购客服会先反问缩小范围,然后推荐可下单的商品卡片。</p>
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
    <!-- Product cards received while streaming (shown below streaming text) -->
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
  padding: 16px 24px;
  max-width: 960px;
  margin: 0 auto;
  width: 100%;
}
.empty-hint {
  text-align: center;
  color: #6b7280;
  padding: 80px 24px;
}
.empty-hint p {
  margin: 6px 0;
}
.empty-hint .sub {
  font-size: 13px;
  color: #9ca3af;
}
.gap {
  display: block;
  height: 4px;
}
</style>
