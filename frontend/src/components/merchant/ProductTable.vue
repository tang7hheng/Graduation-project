<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElTable, ElTableColumn, ElTag, ElButton, ElIcon, ElEmpty, ElDialog, ElForm, ElFormItem, ElInput, ElInputNumber } from 'element-plus'
import { Delete, Picture, Edit } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useMerchantProductsStore } from '@/stores/merchantProducts'
import type { ProductOut } from '@/api/client'

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
  try {
    await ElMessageBox.confirm('确认下架该商品?将同步从客服知识库移除。', '下架商品', {
      confirmButtonText: '确认下架',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await store.remove(id)
  } catch { /* cancelled */ }
}

// === Edit dialog ===
const editVisible = ref(false)
const editingId = ref('')
const editForm = reactive({
  name: '',
  description: '',
  detail_content: '',
  price: '',
  specs: '',
  stock: 0,
  image_url: '',
})

function openEdit(row: ProductOut) {
  editingId.value = row.id
  editForm.name = row.name
  editForm.description = row.description || ''
  editForm.detail_content = row.detail_content || ''
  editForm.price = row.price || ''
  editForm.specs = row.specs || ''
  editForm.stock = row.stock || 0
  editForm.image_url = row.image_url || ''
  editVisible.value = true
}

async function saveEdit() {
  if (!editForm.name.trim()) {
    ElMessage.warning('商品名称不能为空')
    return
  }
  try {
    await store.update(editingId.value, { ...editForm })
    editVisible.value = false
  } catch { /* error already toasted */ }
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
      <el-table-column label="详细介绍" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.detail_content" type="success" size="small" effect="light">已填写</el-tag>
          <el-tag v-else type="info" size="small" effect="plain">未填写</el-tag>
        </template>
      </el-table-column>
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
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button
            type="primary"
            :icon="Edit"
            size="small"
            link
            @click="openEdit(row)"
          >
            编辑
          </el-button>
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

    <!-- Edit Dialog -->
    <el-dialog v-model="editVisible" title="编辑商品" width="640px" :close-on-click-modal="false">
      <el-form :model="editForm" label-width="100px" label-position="right">
        <el-form-item label="商品名称">
          <el-input v-model="editForm.name" placeholder="商品名称" />
        </el-form-item>
        <el-form-item label="商品描述">
          <el-input v-model="editForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="功能与政策">
          <el-input v-model="editForm.detail_content" type="textarea" :rows="6" placeholder="功能介绍、使用说明、售后政策等" />
        </el-form-item>
        <el-form-item label="规格参数">
          <el-input v-model="editForm.specs" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="价格">
          <el-input v-model="editForm.price" />
        </el-form-item>
        <el-form-item label="库存">
          <el-input-number v-model="editForm.stock" :min="0" :step="10" />
        </el-form-item>
        <el-form-item label="图片 URL">
          <el-input v-model="editForm.image_url" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="store.submitting" @click="saveEdit">保存修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.table-card { background: var(--bg-surface); border-radius: var(--radius-md); padding: 16px; box-shadow: var(--shadow-sm); border: 1px solid var(--border-base); }
.header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.header .title { font-weight: 700; font-size: 15px; color: var(--text-primary); }
.product-thumb { width: 40px; height: 40px; object-fit: cover; border-radius: var(--radius-sm); }
.img-placeholder { font-size: 28px; color: var(--text-tertiary); }
</style>
