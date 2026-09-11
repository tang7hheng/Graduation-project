<script setup lang="ts">
import { ref } from 'vue'
import { ElInput, ElButton } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'

const props = defineProps<{
  disabled?: boolean
}>()
const emit = defineEmits<{
  (e: 'send', text: string): void
  (e: 'stop'): void
}>()

const text = ref('')

function handleSend() {
  const t = text.value.trim()
  if (!t) return
  emit('send', t)
  text.value = ''
}

function onKeydown(e: KeyboardEvent) {
  // Enter to send, Shift+Enter for newline
  if (e.key === 'Enter' && !e.shiftKey) {
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
      placeholder="请输入您的问题(Enter 发送,Shift+Enter 换行)"
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
  gap: 8px;
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #e5e7eb;
}
.chat-input :deep(.el-textarea) {
  flex: 1;
}
</style>
