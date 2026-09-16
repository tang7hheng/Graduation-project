<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  ElDialog, ElForm, ElFormItem, ElInput, ElInputNumber, ElButton,
  ElDescriptions, ElDescriptionsItem, ElImage,
} from 'element-plus'
import type { ProductCard } from '@/api/client'
import { useOrdersStore } from '@/stores/orders'
import { useChatStore } from '@/stores/chat'

const props = defineProps<{ modelValue: boolean; product: ProductCard | null }>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'ordered'): void
}>()

const orders = useOrdersStore()
const chat = useChatStore()

const quantity = ref(1)
const remark = ref('')
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

watch(() => props.product?.id, () => { quantity.value = 1; remark.value = '' })

function parsePrice(p: string): number {
  const cleaned = (p || '').replace(/[^\d.]/g, '')
  return cleaned ? parseFloat(cleaned) : 0
}

const total = computed(() => {
  if (!props.product) return '0.00'
  return (parsePrice(props.product.price) * quantity.value).toFixed(2)
})

async function submit() {
  if (!props.product) return
  const order = await orders.placeOrder({
    session_id: chat.currentSessionId || undefined,
    product_id: props.product.id,
    quantity: quantity.value,
    remark: remark.value,
  })
  if (order) {
    dialogVisible.value = false
    emit('ordered')
  }
}
</script>

<template>
  <el-dialog v-model="dialogVisible" title="确认订单" width="460px" :close-on-click-modal="false">
    <div v-if="product" class="order-dialog-body">
      <div class="product-preview">
        <el-image v-if="product.image_url" :src="product.image_url" class="thumb" fit="cover" />
        <div v-else class="thumb-fallback">购</div>
        <div class="info">
          <div class="name">{{ product.name }}</div>
          <div class="price">¥{{ product.price || '—' }}</div>
        </div>
      </div>

      <el-descriptions :column="1" border size="small" class="desc">
        <el-descriptions-item label="规格">{{ product.specs || '—' }}</el-descriptions-item>
        <el-descriptions-item label="描述">{{ product.description || '—' }}</el-descriptions-item>
      </el-descriptions>

      <el-form label-width="80px" class="form">
        <el-form-item label="数量">
          <el-input-number v-model="quantity" :min="1" :max="99" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="remark" type="textarea" :rows="2" placeholder="选填,如颜色偏好、配送要求" />
        </el-form-item>
        <el-form-item label="合计">
          <span class="total">¥{{ total }}</span>
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="orders.placing" @click="submit">提交订单</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.order-dialog-body { display: flex; flex-direction: column; gap: 16px; }
.product-preview {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: var(--bg-muted);
  border-radius: var(--radius-sm);
}
.thumb { width: 72px; height: 72px; border-radius: var(--radius-sm); flex-shrink: 0; }
.thumb-fallback {
  width: 72px; height: 72px;
  background: var(--accent-primary-light);
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 28px; color: var(--accent-primary);
  flex-shrink: 0;
}
.info { flex: 1; }
.info .name { font-weight: 700; font-size: 15px; color: var(--text-primary); margin-bottom: 6px; }
.info .price { color: var(--accent-price); font-weight: 700; font-size: 16px; }
.total { color: var(--accent-price); font-weight: 800; font-size: 18px; }
</style>
