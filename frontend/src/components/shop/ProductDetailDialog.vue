<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElDialog, ElImage, ElButton, ElInputNumber, ElDescriptions, ElDescriptionsItem, ElTag } from 'element-plus'
import { ShoppingCart } from '@element-plus/icons-vue'
import type { ProductOut } from '@/api/client'
import { useCartStore } from '@/stores/cart'

const props = defineProps<{ modelValue: boolean; product: ProductOut | null }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>()

const cart = useCartStore()
const quantity = ref(1)

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

watch(() => props.product?.id, () => { quantity.value = 1 })

function addToCart() { if (!props.product) return; cart.add(props.product, quantity.value) }
function buyNow() {
  if (!props.product) return
  cart.add(props.product, quantity.value)
  cart.openDrawer()
  dialogVisible.value = false
}
</script>

<template>
  <el-dialog v-model="dialogVisible" title="商品详情" width="640px" :close-on-click-modal="true">
    <div v-if="product" class="detail">
      <div class="left">
        <el-image v-if="product.image_url" :src="product.image_url" fit="cover" class="big-img">
          <template #error><div class="img-fallback big-fallback">购</div></template>
        </el-image>
        <div v-else class="img-fallback big-fallback">购</div>
      </div>
      <div class="right">
        <h2 class="name">{{ product.name }}</h2>
        <div class="price-row">
          <span class="price" v-if="product.price">¥{{ product.price }}</span>
          <span v-else class="price-na">价格面议</span>
          <el-tag size="small" type="success" effect="light">库存充足</el-tag>
        </div>
        <el-descriptions :column="1" border size="small" class="desc">
          <el-descriptions-item label="规格">{{ product.specs || '—' }}</el-descriptions-item>
          <el-descriptions-item label="商品描述">{{ product.description || '—' }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="product.detail_content" class="detail-content">
          <h3 class="section-title">功能介绍与使用说明</h3>
          <div class="content-text">{{ product.detail_content }}</div>
        </div>
        <div class="qty-row">
          <span class="qty-label">数量</span>
          <el-input-number v-model="quantity" :min="1" :max="99" />
        </div>
      </div>
    </div>
    <template #footer>
      <el-button @click="dialogVisible = false">关闭</el-button>
      <el-button :icon="ShoppingCart" @click="addToCart">加入购物车</el-button>
      <el-button type="primary" @click="buyNow">立即购买</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.detail { display: flex; gap: 24px; }
.left { flex-shrink: 0; }
.big-img { width: 240px; height: 240px; border-radius: var(--radius-md); overflow: hidden; }
.img-fallback {
  display: flex; align-items: center; justify-content: center;
  background: var(--bg-muted); border-radius: var(--radius-md);
  font-weight: 800; color: var(--text-tertiary);
}
.big-fallback { width: 240px; height: 240px; font-size: 64px; }
.right { flex: 1; display: flex; flex-direction: column; gap: 12px; }
.name { margin: 0; font-size: 20px; font-weight: 800; color: var(--text-primary); }
.price-row { display: flex; align-items: center; gap: 12px; }
.price { font-size: 26px; font-weight: 800; color: var(--accent-price); }
.price-na { font-size: 16px; color: var(--text-tertiary); }
.qty-row { display: flex; align-items: center; gap: 12px; margin-top: 8px; }
.qty-label { font-size: 14px; color: var(--text-secondary); font-weight: 600; }
.detail-content { margin-top: 8px; }
.section-title { font-size: 14px; font-weight: 700; color: var(--text-primary); margin: 0 0 8px; }
.content-text { font-size: 13px; color: var(--text-secondary); line-height: 1.8; white-space: pre-wrap; background: var(--bg-muted); padding: 12px; border-radius: var(--radius-sm); }
</style>
