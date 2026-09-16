<script setup lang="ts">
import { ElTable, ElTableColumn, ElTag, ElButton, ElIcon } from 'element-plus'
import { Delete, Refresh } from '@element-plus/icons-vue'
import type { DocOut } from '@/api/client'
import { useKnowledgeStore } from '@/stores/knowledge'

const store = useKnowledgeStore()

function statusTag(status: string) {
  return status === 'indexed'
    ? { type: 'success' as const, label: '已索引' }
    : { type: 'danger' as const, label: '失败' }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN')
}

async function remove(id: string) {
  if (!confirm('确认删除此文档及对应向量?')) return
  await store.remove(id)
}

async function rebuild() {
  if (!confirm('确认重建索引?会清空当前 collection 并重新索引所有已上传文档,可能耗时较长。')) return
  await store.rebuild()
}
</script>

<template>
  <div class="table-card">
    <div class="header">
      <span class="title">文档列表 ({{ store.documents.length }})</span>
      <el-button
        type="warning"
        :icon="Refresh"
        size="small"
        :loading="store.loading"
        @click="rebuild"
      >
        重建索引
      </el-button>
    </div>
    <el-table :data="store.documents" empty-text="暂无文档" v-loading="store.loading">
      <el-table-column prop="filename" label="文件名" min-width="220" />
      <el-table-column prop="doc_type" label="类型" width="90" />
      <el-table-column prop="chunk_count" label="分块数" width="90" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status).type" size="small">
            {{ statusTag(row.status).label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="上传时间" width="180">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button
            type="danger"
            :icon="Delete"
            size="small"
            link
            @click="remove(row.id)"
          />
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.table-card { background: var(--bg-surface); border-radius: var(--radius-md); padding: 16px; box-shadow: var(--shadow-sm); border: 1px solid var(--border-base); }
.header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.header .title { font-weight: 700; font-size: 15px; color: var(--text-primary); }
</style>
