<script setup lang="ts">
import { ref } from 'vue'
import { ElUpload, ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useKnowledgeStore } from '@/stores/knowledge'

const knowledge = useKnowledgeStore()
const dragOver = ref<boolean>(false)

const ACCEPT = ['.pdf', '.docx', '.xlsx', '.json', '.md', '.txt']

function beforeUpload(file: File): boolean {
  const ext = '.' + (file.name.split('.').pop() || '').toLowerCase()
  if (!ACCEPT.includes(ext)) {
    ElMessage.warning(`不支持的文件类型 ${ext}:支持 ${ACCEPT.join(' ')}`)
    return false
  }
  return true
}

async function customRequest(opts: any) {
  const { file, onSuccess, onError } = opts
  try {
    await knowledge.upload(file)
    onSuccess?.({})
  } catch (e: any) {
    onError?.(e)
  }
}

function onDrop(e: DragEvent) {
  dragOver.value = false
  const files = e.dataTransfer?.files
  if (!files) return
  for (const f of Array.from(files)) {
    if (beforeUpload(f)) knowledge.upload(f)
  }
}

function onDragOver() {
  dragOver.value = true
}
function onDragLeave() {
  dragOver.value = false
}
</script>

<template>
  <div
    class="dropzone"
    :class="{ active: dragOver }"
    @dragover.prevent="onDragOver"
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
  >
    <el-upload
      drag
      multiple
      :show-file-list="false"
      :before-upload="beforeUpload"
      :http-request="customRequest"
      :accept="ACCEPT.join(',')"
    >
      <el-icon class="icon"><UploadFilled /></el-icon>
      <div class="title">点击或拖拽文件到此处上传</div>
      <div class="sub">支持 {{ ACCEPT.join('、') }} 等</div>
    </el-upload>
  </div>
</template>

<style scoped>
.dropzone {
  border: 2px dashed var(--border-strong); border-radius: var(--radius-md);
  padding: 24px; background: var(--bg-surface); margin-bottom: 16px; transition: all 0.2s;
}
.dropzone.active { border-color: var(--accent-primary); background: var(--accent-primary-light); }
.dropzone :deep(.el-upload-dragger) { width: 100%; padding: 20px; border: none; background: transparent; }
.icon { font-size: 40px; color: var(--accent-primary); margin-bottom: 8px; }
.title { color: var(--text-primary); font-size: 14px; margin-bottom: 4px; font-weight: 600; }
.sub { color: var(--text-tertiary); font-size: 12px; }
</style>
