<script setup lang="ts">
import { ElButton, ElIcon, ElEmpty, ElScrollbar } from 'element-plus'
import { Plus, Delete, ChatDotRound } from '@element-plus/icons-vue'
import { useSessionsStore } from '@/stores/sessions'

const sessions = useSessionsStore()

function select(id: string) {
  sessions.select(id)
}

async function createNew() {
  await sessions.create()
}

async function remove(id: string, e: Event) {
  e.stopPropagation()
  if (!confirm('确认删除该会话?所有消息将一并删除。')) return
  await sessions.remove(id)
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <span class="title">会话历史</span>
      <el-button type="primary" :icon="Plus" size="small" @click="createNew">新建会话</el-button>
    </div>
    <el-scrollbar class="session-list">
      <el-empty v-if="sessions.list.length === 0" description="暂无会话" :image-size="60" />
      <div
        v-for="s in sessions.list"
        :key="s.id"
        class="session-item"
        :class="{ active: s.id === sessions.currentId }"
        @click="select(s.id)"
      >
        <el-icon class="dot"><ChatDotRound /></el-icon>
        <div class="meta">
          <div class="title">{{ s.title || '新会话' }}</div>
          <div class="time">{{ new Date(s.updated_at).toLocaleString('zh-CN') }}</div>
        </div>
        <el-icon class="del" @click="remove(s.id, $event)"><Delete /></el-icon>
      </div>
    </el-scrollbar>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 280px;
  height: 100%;
  background: #1f2937;
  color: #e5e7eb;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.sidebar-header {
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #374151;
}
.sidebar-header .title {
  font-weight: 600;
  font-size: 14px;
}
.session-list {
  flex: 1;
}
.session-item {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  border-bottom: 1px solid #374151;
  transition: background 0.15s;
}
.session-item:hover {
  background: #374151;
}
.session-item.active {
  background: #4b5563;
}
.session-item .dot {
  flex-shrink: 0;
  color: #60a5fa;
}
.session-item .meta {
  flex: 1;
  min-width: 0;
}
.session-item .title {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.session-item .time {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}
.session-item .del {
  color: #9ca3af;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
}
.session-item:hover .del {
  opacity: 1;
}
.session-item .del:hover {
  color: #f87171;
}
</style>
