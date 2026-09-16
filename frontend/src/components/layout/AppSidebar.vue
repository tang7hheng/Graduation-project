<script setup lang="ts">
import { ElButton, ElIcon, ElEmpty, ElScrollbar, ElMessageBox } from 'element-plus'
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
  try {
    await ElMessageBox.confirm('确认删除该会话?所有消息将一并删除。', '删除会话', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await sessions.remove(id)
  } catch {
    // user cancelled — do nothing
  }
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <span class="title">会话历史</span>
      <el-button type="primary" :icon="Plus" size="small" @click="createNew">新建</el-button>
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
  background: var(--bg-surface);
  border-right: 1px solid var(--border-base);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.sidebar-header {
  padding: 18px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-light);
}
.sidebar-header .title {
  font-weight: 700;
  font-size: 15px;
  color: var(--text-primary);
}
.session-list { flex: 1; }
.session-item {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-light);
  transition: background 0.15s ease;
}
.session-item:hover {
  background: var(--bg-hover);
}
.session-item.active {
  background: var(--accent-primary-light);
  border-left: 3px solid var(--accent-primary);
  padding-left: 13px;
}
.session-item .dot {
  flex-shrink: 0;
  color: var(--accent-primary);
  font-size: 14px;
}
.session-item .meta { flex: 1; min-width: 0; }
.session-item .title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.session-item .time {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 2px;
}
.session-item .del {
  color: var(--text-tertiary);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
}
.session-item:hover .del { opacity: 1; }
.session-item .del:hover { color: var(--accent-danger); }
</style>
