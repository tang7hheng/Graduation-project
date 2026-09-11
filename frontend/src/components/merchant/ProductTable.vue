<script setup lang="ts">
import { ElTable, ElTableColumn, ElTag, ElButton, ElIcon, ElEmpty } from 'element-plus'
import { Delete, Picture } from '@element-plus/icons-vue'
import { useMerchantProductsStore } from '@/stores/merchantProducts'

const store = useMerchantProductsStore()

function statusTag(status: string) {
  return status === 'indexed'
    ? { type: 'success' as const, label: '已索引' }
    : { type: 'danger' as const, label: '失败' }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN')
}

async function remove(id: string) {
  if (!confirm('确认下架该商品?将同步从客服知识库移除。')) return
  await store.remove(id)
}
</script>

<template>
  <div class="table-card">
    <div class="header">
      <span class="title">我的商品 ({{ store.products.length }})</span>
    </div>
    <el-table
      :data="store.products"
      empty-text="暂无商品,请使用上方表单上架"
      v-loading="store.loading"
    >
      <el-table-column label="图片" width="80">
        <template #default="{ row }">
          <el-icon v-if="!row.image_url" class="img-placeholder"><Picture /></el-icon>
          <img
            v-else
            :src="row.image_url"
            class="product-thumb"
            @error="(e: any) => (e.target.style.display = 'none')"
          />
        </template>
      </el-table-column>
      <el-table-column prop="name" label="商品名称" min-width="160" />
      <el-table-column prop="price" label="价格" width="120" />
      <el-table-column prop="stock" label="库存" width="80" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status).type" size="small">
            {{ statusTag(row.status).label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="上架时间" width="180">
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
          >
            下架
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="store.products.length === 0 && !store.loading" :image-size="80" />
  </div>
</template>

<style scoped>
.table-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.header .title {
  font-weight: 600;
  font-size: 15px;
  color: #1f2937;
}
.product-thumb {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 4px;
}
.img-placeholder {
  font-size: 28px;
  color: #d1d5db;
}
</style>
