<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElDrawer, ElEmpty, ElImage, ElInputNumber, ElButton, ElInput } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { useCartStore } from '@/stores/cart'
import { useRouter } from 'vue-router'

const cart = useCartStore()
const router = useRouter()
const remark = ref('')

function parsePrice(p: string): number {
  const cleaned = (p || '').replace(/[^\d.]/g, '')
  return cleaned ? parseFloat(cleaned) : 0
}

function lineTotal(price: string, qty: number): string {
  return (parsePrice(price) * qty).toFixed(2)
}

// Group lines by merchant for display
const groupedLines = computed(() => {
  const map = new Map<string, { merchant_id: string; lines: typeof cart.lines }>()
  for (const line of cart.lines) {
    const key = line.merchant_id
    if (!map.has(key)) {
      map.set(key, { merchant_id: key, lines: [] as typeof cart.lines })
    }
    map.get(key)!.lines.push(line)
  }
  return Array.from(map.values())
})

async function checkout() {
  const ok = await cart.checkout(remark.value)
  if (ok) {
    remark.value = ''
    // Navigate to orders page to see the result
    router.push('/orders')
  }
}
</script>

<template>
  <el-drawer
    v-model="cart.drawerVisible"
    title="购物车"
    direction="rtl"
    size="420px"
  >
    <el-empty v-if="cart.lines.length === 0" description="购物车为空" />
    <div v-else class="cart-body">
      <div
        v-for="group in groupedLines"
        :key="group.merchant_id"
        class="merchant-group"
      >
        <div class="merchant-label">商家:{{ group.merchant_id.slice(0, 8) }}</div>
        <div v-for="line in group.lines" :key="line.product_id" class="cart-line">
          <el-image
            v-if="line.image_url"
            :src="line.image_url"
            fit="cover"
            class="thumb"
          />
          <div v-else class="thumb-fallback">📦</div>
          <div class="info">
            <div class="name">{{ line.name }}</div>
            <div class="specs" v-if="line.specs">{{ line.specs }}</div>
            <div class="price-row">
              <span class="price">¥{{ line.price || '面议' }}</span>
              <span class="line-total">小计 ¥{{ lineTotal(line.price, line.quantity) }}</span>
            </div>
            <div class="qty-row">
              <el-input-number
                :model-value="line.quantity"
                :min="1"
                :max="99"
                size="small"
                @change="(v: any) => cart.updateQty(line.product_id, v)"
              />
              <el-button
                :icon="Delete"
                size="small"
                link
                type="danger"
                @click="cart.remove(line.product_id)"
              >
                移除
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="remark-row">
        <span class="label">订单备注</span>
        <el-input
          v-model="remark"
          type="textarea"
          :rows="2"
          placeholder="选填"
          size="small"
        />
      </div>
    </div>

    <template #footer>
      <div v-if="cart.lines.length > 0" class="checkout-footer">
        <div class="total-row">
          <span>合计:</span>
          <span class="total-amount">¥{{ cart.totalAmount }}</span>
        </div>
        <el-button
          type="primary"
          class="checkout-btn"
          :loading="cart.checkingOut"
          @click="checkout"
        >
          结算 ({{ cart.count }}件)
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<style scoped>
.cart-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  overflow-y: auto;
}
.merchant-group {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}
.merchant-label {
  padding: 8px 12px;
  background: #f9fafb;
  font-size: 12px;
  color: #6b7280;
  border-bottom: 1px solid #e5e7eb;
}
.cart-line {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
}
.cart-line:last-child {
  border-bottom: none;
}
.thumb {
  width: 60px;
  height: 60px;
  border-radius: 6px;
  flex-shrink: 0;
}
.thumb-fallback {
  width: 60px;
  height: 60px;
  background: #e5e7eb;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}
.info {
  flex: 1;
  min-width: 0;
}
.name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 2px;
}
.specs {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 4px;
}
.price-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.price {
  color: #dc2626;
  font-size: 13px;
}
.line-total {
  font-size: 13px;
  color: #4b5563;
}
.qty-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.remark-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.remark-row .label {
  font-size: 13px;
  color: #4b5563;
}
.checkout-footer {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 0;
}
.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 15px;
}
.total-amount {
  font-size: 20px;
  font-weight: 700;
  color: #dc2626;
}
.checkout-btn {
  width: 100%;
}
</style>
