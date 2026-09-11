<script setup lang="ts">
import { ElCard, ElCollapse, ElCollapseItem, ElTag } from 'element-plus'
import type { ChatSource } from '@/api/client'

defineProps<{
  sources: ChatSource[]
}>()

function formatScore(s: number): string {
  return (s * 100).toFixed(1) + '%'
}

function isProduct(s: ChatSource): boolean {
  return s.kind === 'product' || !!s.product_id
}

function itemTitle(s: ChatSource, i: number): string {
  const prefix = `[${i + 1}]`
  return isProduct(s)
    ? `${prefix} ${s.title}${s.price ? '(¥' + s.price + ')' : ''}`
    : `${prefix} ${s.title}${s.page ? '(第' + s.page + '页)' : ''}`
}
</script>

<template>
  <el-card v-if="sources.length" class="source-card" shadow="never">
    <template #header>
      <span class="header-title">引用来源 ({{ sources.length }})</span>
    </template>
    <el-collapse>
      <el-collapse-item
        v-for="(src, i) in sources"
        :key="i"
        :title="itemTitle(src, i)"
        :name="i"
      >
        <div class="source-body">
          <div class="tags">
            <el-tag size="small" :type="isProduct(src) ? 'warning' : 'success'">
              {{ isProduct(src) ? '商品' : '文档' }}
            </el-tag>
            <el-tag size="small" type="info">相似度 {{ formatScore(src.score) }}</el-tag>
          </div>
          <div class="snippet">{{ src.snippet }}</div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </el-card>
</template>

<style scoped>
.source-card {
  margin: 8px 0 16px;
  background: #f9fafb;
  border: 1px dashed #d1d5db;
}
.header-title {
  font-weight: 600;
  font-size: 13px;
  color: #4b5563;
}
.source-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.tags {
  display: flex;
  gap: 6px;
}
.snippet {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
  padding: 6px 8px;
  background: #fff;
  border-radius: 4px;
  border-left: 3px solid #9ca3af;
}
</style>
