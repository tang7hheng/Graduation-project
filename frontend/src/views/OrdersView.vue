<script setup lang="ts">
import { onMounted } from 'vue'
import { ElTable, ElTableColumn, ElTag, ElButton, ElEmpty, ElImage } from 'element-plus'
import { useOrdersStore } from '@/stores/orders'
import { useChatStore } from '@/stores/chat'

const orders = useOrdersStore()
const chat = useChatStore()

onMounted(async () => { await orders.fetchList(chat.currentSessionId || undefined) })

function statusInfo(status: string) {
  switch (status) {
    case 'paid': return { type: 'success' as const, label: '已支付' }
    case 'cancelled': return { type: 'info' as const, label: '已取消' }
    default: return { type: 'warning' as const, label: '待支付' }
  }
}
function formatDate(iso: string) { return new Date(iso).toLocaleString('zh-CN') }
function shortId(id: string) { return id.slice(0, 8) }
</script>

<template>
  <div class="orders-layout">
    <div class="content">
      <h2 class="title">我的订单</h2>
      <el-empty v-if="!orders.loading && orders.orders.length === 0" description="暂无订单">
        <p class="empty-hint">在智能问答中点击商品卡片即可下单</p>
      </el-empty>
      <el-table v-else :data="orders.orders" v-loading="orders.loading" empty-text="暂无订单" class="orders-table">
        <el-table-column label="订单号" width="120">
          <template #default="{ row }">{{ shortId(row.id) }}</template>
        </el-table-column>
        <el-table-column label="商品" min-width="240">
          <template #default="{ row }">
            <div v-for="item in row.items" :key="item.id" class="item-row">
              <el-image v-if="item.image_url" :src="item.image_url" class="thumb" fit="cover" />
              <div v-else class="thumb-fallback">购</div>
              <div class="meta">
                <div class="name">{{ item.product_name }}</div>
                <div class="sub">x{{ item.quantity }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="total_amount" label="合计" width="120">
          <template #default="{ row }">¥{{ row.total_amount }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusInfo(row.status).type" size="small">{{ statusInfo(row.status).label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="下单时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" type="primary" size="small" @click="orders.pay(row.id)">立即支付</el-button>
            <el-button v-if="row.status === 'pending'" type="info" size="small" link @click="orders.cancel(row.id)">取消</el-button>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.orders-layout { padding: 24px; height: 100%; overflow: auto; background: var(--bg-base); }
.content { max-width: 960px; margin: 0 auto; }
.title { margin: 0 0 20px; font-size: 22px; font-weight: 800; color: var(--text-primary); }
.empty-hint { color: var(--text-tertiary); font-size: 13px; }
.orders-table { border-radius: var(--radius-md); overflow: hidden; border: 1px solid var(--border-base); }
.orders-table :deep(th.el-table__cell) {
  background: var(--bg-muted) !important; color: var(--text-primary) !important; font-weight: 700;
}
.item-row { display: flex; gap: 8px; align-items: center; padding: 4px 0; }
.thumb { width: 40px; height: 40px; border-radius: var(--radius-sm); flex-shrink: 0; }
.thumb-fallback {
  width: 40px; height: 40px; background: var(--accent-primary-light); border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 18px; color: var(--accent-primary);
}
.meta { flex: 1; }
.name { font-size: 13px; color: var(--text-primary); }
.sub { font-size: 12px; color: var(--text-tertiary); }
.muted { color: var(--text-tertiary); }
</style>
