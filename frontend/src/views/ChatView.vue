<script setup lang="ts">
import { onMounted, watch, computed, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { ElAlert } from 'element-plus'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import MessageList from '@/components/chat/MessageList.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import SourceCitations from '@/components/chat/SourceCitations.vue'
import { useSessionsStore } from '@/stores/sessions'
import { useChatStore } from '@/stores/chat'

const sessions = useSessionsStore()
const chat = useChatStore()
const { currentId } = storeToRefs(sessions)
const { isStreaming, currentSources } = storeToRefs(chat)

watch(currentId, async (id) => {
  if (id) {
    await chat.loadSession(id)
    // If there's a pending query from another page, auto-send it
    if (chat.pendingQuery) {
      const q = chat.pendingQuery
      chat.pendingQuery = ''
      await nextTick()
      await chat.sendMessage(q)
    }
  } else {
    chat.reset()
  }
})

onMounted(async () => {
  await sessions.fetchList()
  if (sessions.list.length > 0 && !currentId.value) {
    await sessions.select(sessions.list[0].id)
  } else if (sessions.list.length === 0) {
    // No sessions — create one so pending query can be sent
    await sessions.create()
  }
  // If there's a pending query, auto-send it
  if (chat.pendingQuery && currentId.value && !isStreaming.value) {
    const q = chat.pendingQuery
    chat.pendingQuery = ''
    await nextTick()
    await chat.sendMessage(q)
  }
})

const hasSession = computed(() => !!currentId.value)
</script>

<template>
  <div class="chat-layout">
    <AppSidebar />
    <div class="chat-main">
      <MessageList
        :messages="chat.messages"
        :streaming-text="chat.streamingText"
        :is-streaming="isStreaming"
        :thinking-message="chat.thinkingMessage"
        :streaming-product-cards="chat.currentProductCards"
        :streaming-sources="chat.currentSources"
      />
      <SourceCitations v-if="!isStreaming && currentSources.length" :sources="currentSources" />
      <el-alert
        v-if="chat.errorMessage"
        :title="chat.errorMessage"
        type="error"
        :closable="true"
        class="error-banner"
      />
      <ChatInput
        :disabled="isStreaming || !hasSession"
        @send="(t) => chat.sendMessage(t)"
        @stop="chat.stopStreaming"
      />
    </div>
  </div>
</template>

<style scoped>
.chat-layout {
  display: flex;
  height: 100%;
  width: 100%;
}
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-width: 0;
}
.error-banner {
  margin: 0 16px;
}
</style>
