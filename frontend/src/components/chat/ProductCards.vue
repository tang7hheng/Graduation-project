<script setup lang="ts">
import { ref } from 'vue'
import { ElCard, ElButton, ElImage, ElIcon, ElTag } from 'element-plus'
import { ShoppingCart } from '@element-plus/icons-vue'
import type { ProductCard } from '@/api/client'
import OrderDialog from './OrderDialog.vue'

defineProps<{
  cards: ProductCard[]
}>()

const dialogVisible = ref(false)
const selectedProduct = ref<ProductCard | null>(null)

function openOrder(p: ProductCard) {
  selectedProduct.value = p
  dialogVisible.value = true
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
      <div class="img-wrap">
        <el-image
          v-if="p.image_url"
          :src="p.image_url"
          fit="cover"
          class="img"
        />
        <div v-else class="img-fallback">📦</div>
        <el-tag class="tag" size="small" type="warning" effect="dark">推荐商品</el-tag>
      </div>
      <div class="info">
        <div class="name">{{ p.name }}</div>
        <div class="specs" v-if="p.specs">{{ p.specs }}</div>
        <div class="footer">
          <span class="price" v-if="p.price">¥{{ p.price }}</span>
          <span v-else class="price-na">价格面议</span>
          <el-button
            type="primary"
            size="small"
            :icon="ShoppingCart"
            @click="openOrder(p)"
          >
            立即购买
          </el-button>
        </div>
      </div>
    </el-card>

    <OrderDialog
      v-model="dialogVisible"
      :product="selectedProduct"
    />
  </div>
</template>

<style scoped>
.cards-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 12px 0 4px;
}
.product-card {
  width: 200px;
  overflow: hidden;
}
.img-wrap {
  position: relative;
  width: 100%;
  height: 120px;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.img {
  width: 100%;
  height: 100%;
}
.img-fallback {
  font-size: 40px;
}
.tag {
  position: absolute;
  top: 6px;
  left: 6px;
}
.info {
  padding: 10px 12px;
}
.name {
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.specs {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.price {
  color: #dc2626;
  font-weight: 700;
  font-size: 15px;
}
.price-na {
  color: #6b7280;
  font-size: 13px;
}
</style>
