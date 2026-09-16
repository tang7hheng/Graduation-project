<script setup lang="ts">
import { onMounted } from 'vue'
import { ElAlert } from 'element-plus'
import UploadDropzone from '@/components/knowledge/UploadDropzone.vue'
import DocumentTable from '@/components/knowledge/DocumentTable.vue'
import { useKnowledgeStore } from '@/stores/knowledge'

const knowledge = useKnowledgeStore()

onMounted(() => {
  knowledge.fetchList()
})
</script>

<template>
  <div class="knowledge-layout">
    <div class="content">
      <el-alert
        type="info"
        :closable="false"
        title="上传的文档将自动分块并写入向量库。每条 FAQ 视为一个独立分块;PDF/Word/MD 按内容分块。"
        show-icon
      />
      <UploadDropzone />
      <DocumentTable />
    </div>
  </div>
</template>

<style scoped>
.knowledge-layout { padding: 24px; height: 100%; overflow: auto; background: var(--bg-base); }
.content { max-width: 960px; margin: 0 auto; display: flex; flex-direction: column; gap: 12px; }
</style>
