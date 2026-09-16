<script setup lang="ts">
import { ref } from 'vue'
import { ElCard, ElButton, ElImage, ElTag } from 'element-plus'
import { ShoppingCart, Goods } from '@element-plus/icons-vue'
import type { ProductCard } from '@/api/client'
import OrderDialog from './OrderDialog.vue'
import { useCartStore } from '@/stores/cart'
import { ElMessage } from 'element-plus'

defineProps<{
  cards: ProductCard[]
}>()

const cart = useCartStore()
const dialogVisible = ref(false)
const selectedProduct = ref<ProductCard | null>(null)

function openOrder(p: ProductCard) {
  selectedProduct.value = p
  dialogVisible.value = true
}

function addToCart(p: ProductCard) {
  if (p.stock_status === '缺货') return
  cart.add(p as any, 1)
  ElMessage.success(`已加入购物车：${p.name.slice(0, 20)}`)
}

function parseSpecs(specs: string): { label: string; value: string }[] {
  if (!specs) return []
  return specs
    .split(/[;；]/)
    .map((s) => s.trim())
    .filter(Boolean)
    .map((pair) => {
      const idx = pair.search(/[:：]/)
      if (idx < 0) return { label: pair, value: '' }
      return {
        label: pair.slice(0, idx).trim(),
        value: pair.slice(idx + 1).trim(),
      }
    })
}

function specsList(p: ProductCard) {
  return parseSpecs(p.specs)
}

function stockTagType(status: string) {
  return status === '充足' ? 'success' : 'danger'
}
</script>

<template>
  <div v-if="cards.length" class="cards-row">
    <el-card
      v-for="p in cards"
      :key="p.id"
      class="product-card"
      shadow="hover"
      :body-style="{ padding: '0' }"
    >
      <div class="card-head">
        <div class="img-wrap">
          <el-image v-if="p.image_url" :src="p.image_url" fit="cover" class="img" />
          <div v-else class="img-fallback">
            <el-icon :size="28"><Goods /></el-icon>
          </div>
        </div>
        <div class="head-text">
          <div class="name" :title="p.name">{{ p.name }}</div>
          <div class="merchant" v-if="p.merchant_name">
            <el-tag size="small" type="info" effect="plain">{{ p.merchant_name }}</el-tag>
          </div>
        </div>
        <el-tag
          class="stock-tag"
          size="small"
          :type="stockTagType(p.stock_status || '充足')"
          effect="light"
        >
          {{ p.stock_status || '充足' }}
        </el-tag>
      </div>

      <div class="desc" v-if="p.description">{{ p.description }}</div>

      <div class="specs" v-if="specsList(p).length">
        <div v-for="(s, i) in specsList(p)" :key="i" class="spec-item">
          <span class="spec-label">{{ s.label }}</span>
          <span class="spec-value">{{ s.value }}</span>
        </div>
      </div>

      <div class="footer">
        <div class="price-block">
          <span class="price" v-if="p.price">¥{{ p.price }}</span>
          <span v-else class="price-na">价格面议</span>
        </div>
        <div class="actions">
          <el-button
            size="small"
            :icon="ShoppingCart"
            :disabled="p.stock_status === '缺货'"
            @click="addToCart(p)"
          >
            加入购物车
          </el-button>
          <el-button
            type="primary"
            size="small"
            :disabled="p.stock_status === '缺货'"
            @click="openOrder(p)"
          >
            立即购买
          </el-button>
        </div>
      </div>
    </el-card>

    <OrderDialog v-model="dialogVisible" :product="selectedProduct" />
  </div>
</template>

<style scoped>
.cards-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin: 12px 0 4px;
  animation: slide-in 0.3s ease-out;
}
.product-card {
  width: 100%;
  overflow: hidden;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-base);
  transition: box-shadow 0.2s, transform 0.2s;
  display: flex;
  flex-direction: column;
}
.product-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}
.card-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}
.img-wrap {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  border-radius: var(--radius-sm);
  background: var(--bg-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.img { width: 100%; height: 100%; }
.img-fallback { color: var(--text-tertiary); }
.head-text { flex: 1; min-width: 0; }
.name {
  font-weight: 700;
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.merchant { font-size: 12px; }
.stock-tag { flex-shrink: 0; align-self: flex-start; }
.desc {
  padding: 8px 14px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-light);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
}
.specs {
  padding: 8px 14px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2px 16px;
  flex-shrink: 0;
}
.spec-item {
  display: flex;
  font-size: 12px;
  line-height: 1.5;
  overflow: hidden;
  white-space: nowrap;
}
.spec-label { color: var(--text-tertiary); flex-shrink: 0; margin-right: 4px; }
.spec-label::after { content: ':'; }
.spec-value {
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
}
.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-top: 1px solid var(--border-light);
  flex-shrink: 0;
  margin-top: auto;
}
.actions {
  display: flex;
  gap: 8px;
}
.price-block { display: flex; align-items: baseline; }
.price {
  color: var(--accent-price);
  font-weight: 800;
  font-size: 18px;
}
.price-na { color: var(--text-tertiary); font-size: 13px; }
</style>
