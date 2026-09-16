<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElInput, ElButton } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'

const props = defineProps<{
  disabled?: boolean
}>()
const emit = defineEmits<{
  (e: 'send', text: string): void
  (e: 'stop'): void
}>()

const chatStore = useChatStore()
// Use store's draftText so input persists across page navigation
const text = ref(chatStore.draftText)

// Sync local text → store on every change
watch(text, (v) => {
  chatStore.draftText = v
})

function handleSend() {
  const t = text.value.trim()
  if (!t) return
  emit('send', t)
  text.value = ''
  chatStore.draftText = ''
}

function onKeydown(e: Event) {
  const ke = e as KeyboardEvent
  if (ke.key === 'Enter' && !ke.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="chat-input">
    <el-input
      v-model="text"
      type="textarea"
      :rows="2"
      :autosize="{ minRows: 2, maxRows: 6 }"
      placeholder="输入您的问题…(Enter 发送, Shift+Enter 换行)"
      resize="none"
      :disabled="disabled"
      @keydown="onKeydown"
    />
    <el-button
      v-if="!disabled"
      type="primary"
      :icon="Promotion"
      @click="handleSend"
    >
      发送
    </el-button>
    <el-button v-else type="danger" @click="emit('stop')">中止</el-button>
  </div>
</template>

<style scoped>
.chat-input {
  display: flex;
  gap: 10px;
  padding: 14px 20px;
  background: var(--bg-surface);
  border-top: 1px solid var(--border-base);
}
.chat-input :deep(.el-textarea) { flex: 1; }
.chat-input :deep(.el-textarea__inner) {
  border-radius: var(--radius-sm);
  border-color: var(--border-base);
  background: var(--bg-surface);
  color: var(--text-primary);
  font-size: 14px;
  padding: 10px 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.chat-input :deep(.el-textarea__inner:focus) {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12);
}
.chat-input :deep(.el-textarea__inner::placeholder) {
  color: var(--text-tertiary);
}
</style>
