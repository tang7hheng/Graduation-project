<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElCard, ElCollapse, ElCollapseItem, ElTag, ElButton, ElIcon } from 'element-plus'
import { Close, ArrowDown, ArrowUp } from '@element-plus/icons-vue'
import type { ChatSource } from '@/api/client'

const props = defineProps<{ sources: ChatSource[] }>()

const activeNames = ref<number[]>([])
const collapsed = ref(true)

function formatScore(s: number): string { return (s * 100).toFixed(1) + '%' }
function isProduct(s: ChatSource): boolean { return s.kind === 'product' || !!s.product_id }
function itemTitle(s: ChatSource, i: number): string {
  const prefix = `[${i + 1}]`
  return isProduct(s)
    ? `${prefix} ${s.title}${s.price ? '(¥' + s.price + ')' : ''}`
    : `${prefix} ${s.title}${s.page ? '(第' + s.page + '页)' : ''}`
}

function toggleAll() {
  if (collapsed.value) {
    activeNames.value = props.sources.map((_, i) => i)
    collapsed.value = false
  } else {
    activeNames.value = []
    collapsed.value = true
  }
}

// 默认折叠
watch(() => props.sources, () => {
  activeNames.value = []
  collapsed.value = true
}, { immediate: true })
</script>

<template>
  <el-card v-if="sources.length" class="source-card" shadow="never">
    <template #header>
      <div class="source-header" @click="toggleAll">
        <span class="header-title">引用来源 ({{ sources.length }})</span>
        <el-button text size="small" class="toggle-btn">
          <el-icon class="header-icon"><component :is="collapsed ? ArrowDown : ArrowUp" /></el-icon>
          <span>{{ collapsed ? '展开' : '收起' }}</span>
        </el-button>
      </div>
    </template>
    <el-collapse v-show="!collapsed" v-model="activeNames">
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
  background: var(--bg-muted, #f8fafc);
  border: 1px solid var(--border-base, #e2e8f0);
  border-radius: var(--radius-md, 10px);
}
.source-card :deep(.el-card__header) {
  background: var(--accent-primary-light, #ede9fe);
  border-bottom: 1px solid var(--border-light, #e2e8f0);
  border-radius: 10px 10px 0 0;
  padding: 8px 14px;
}
.source-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}
.header-title {
  font-weight: 700;
  font-size: 13px;
  color: var(--accent-primary-dark, #4f46e5);
}
.toggle-btn {
  flex-shrink: 0;
}
.header-icon {
  font-size: 14px;
  margin-right: 2px;
}
.source-card :deep(.el-collapse) {
  border-top: none;
  max-height: 280px;
  overflow-y: auto;
}
.source-card :deep(.el-collapse-item__header) {
  font-size: 13px;
  height: 36px;
  line-height: 36px;
}
.source-body { display: flex; flex-direction: column; gap: 6px; }
.tags { display: flex; gap: 6px; }
.snippet {
  font-size: 13px;
  color: var(--text-secondary, #64748b);
  line-height: 1.6;
  padding: 8px 10px;
  background: var(--bg-surface, #fff);
  border-radius: 6px;
  border-left: 3px solid var(--accent-primary, #4f46e5);
}
</style>
