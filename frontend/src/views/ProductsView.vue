<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { ElCard, ElEmpty, ElTag, ElInput, ElButton, ElImage } from 'element-plus'
import { Search, ShoppingCart, Plus } from '@element-plus/icons-vue'
import type { ProductOut } from '@/api/client'
import { listAllProducts } from '@/api/products'
import { useCartStore } from '@/stores/cart'
import OrderDialog from '@/components/chat/OrderDialog.vue'
import ProductDetailDialog from '@/components/shop/ProductDetailDialog.vue'

const cart = useCartStore()

const products = ref<ProductOut[]>([])
const loading = ref(false)
const keyword = ref('')
const sortMode = ref<'default' | 'price-asc' | 'price-desc'>('default')

// Order dialog state (for "立即购买" quick path)
const orderDialogVisible = ref(false)
const selectedProductCard = ref<any>(null)

// Product detail dialog state
const detailVisible = ref(false)
const detailProduct = ref<ProductOut | null>(null)

onMounted(async () => {
  loading.value = true
  try {
    products.value = await listAllProducts()
  } finally {
    loading.value = false
  }
})

function parsePrice(p: string): number {
  const cleaned = (p || '').replace(/[^\d.]/g, '')
  return cleaned ? parseFloat(cleaned) : 0
}

const filtered = computed(() => {
  let list = products.value
  const k = keyword.value.trim().toLowerCase()
  if (k) {
    list = list.filter(
      (p) =>
        p.name.toLowerCase().includes(k) ||
        p.description.toLowerCase().includes(k) ||
        p.specs.toLowerCase().includes(k),
    )
  }
  if (sortMode.value === 'price-asc') {
    list = [...list].sort((a, b) => parsePrice(a.price) - parsePrice(b.price))
  } else if (sortMode.value === 'price-desc') {
    list = [...list].sort((a, b) => parsePrice(b.price) - parsePrice(a.price))
  }
  return list
})

function addToCart(p: ProductOut) {
  cart.add(p, 1)
}

function buyNow(p: ProductOut) {
  // Quick path: reuse OrderDialog (single-item checkout)
  selectedProductCard.value = {
    id: p.id,
    merchant_id: p.merchant_id,
    name: p.name,
    description: p.description,
    price: p.price,
    specs: p.specs,
    image_url: p.image_url,
  }
  orderDialogVisible.value = true
}

function openDetail(p: ProductOut) {
  detailProduct.value = p
  detailVisible.value = true
}
</script>

<template>
  <div class="shop-layout">
    <div class="content">
      <!-- Banner -->
      <div class="banner">
        <div class="banner-text">
          <h1 class="banner-title">智能商城</h1>
          <p class="banner-sub">所有商品均由入驻商户发布,有问题可随时咨询智能客服</p>
        </div>
        <router-link to="/chat" class="banner-cta">
          <el-button type="primary" round>咨询客服</el-button>
        </router-link>
      </div>

      <!-- Toolbar -->
      <div class="toolbar">
        <el-input
          v-model="keyword"
          placeholder="搜索商品名称 / 描述 / 规格"
          :prefix-icon="Search"
          clearable
          class="search"
        />
        <div class="sort">
          <span class="sort-label">排序:</span>
          <el-button
            size="small"
            :type="sortMode === 'default' ? 'primary' : 'default'"
            @click="sortMode = 'default'"
          >
            综合
          </el-button>
          <el-button
            size="small"
            :type="sortMode === 'price-asc' ? 'primary' : 'default'"
            @click="sortMode = 'price-asc'"
          >
            价格↑
          </el-button>
          <el-button
            size="small"
            :type="sortMode === 'price-desc' ? 'primary' : 'default'"
            @click="sortMode = 'price-desc'"
          >
            价格↓
          </el-button>
        </div>
      </div>

      <!-- Products grid -->
      <el-empty v-if="!loading && filtered.length === 0" description="暂无商品" />
      <div class="grid" v-loading="loading">
        <el-card
          v-for="p in filtered"
          :key="p.id"
          class="product-card"
          shadow="hover"
          :body-style="{ padding: '0' }"
        >
          <div class="img-wrap" @click="openDetail(p)">
            <el-image
              v-if="p.image_url"
              :src="p.image_url"
              fit="cover"
              class="img"
            >
              <template #error>
                <div class="img-fallback">📦</div>
              </template>
            </el-image>
            <div v-else class="img-fallback">📦</div>
            <el-tag class="tag" size="small" type="success" effect="dark">
              库存充足
            </el-tag>
          </div>
          <div class="info">
            <div class="name" :title="p.name" @click="openDetail(p)">{{ p.name }}</div>
            <div class="desc">{{ p.description || '暂无描述' }}</div>
            <div class="specs" v-if="p.specs">{{ p.specs }}</div>
            <div class="footer">
              <span class="price" v-if="p.price">¥{{ p.price }}</span>
              <span v-else class="price-na">价格面议</span>
            </div>
            <div class="actions">
              <el-button
                size="small"
                :icon="Plus"
                @click="addToCart(p)"
              >
                加入购物车
              </el-button>
              <el-button
                type="primary"
                size="small"
                :icon="ShoppingCart"
                @click="buyNow(p)"
              >
                立即购买
              </el-button>
            </div>
          </div>
        </el-card>
      </div>

      <div class="hint">
        没找到心仪商品?前往 <router-link to="/chat" class="link">智能问答</router-link> 告诉客服你的需求,客服会反问缩小范围后推荐商品卡片。
      </div>
    </div>

    <!-- Single-item quick checkout (legacy path) -->
    <OrderDialog
      v-model="orderDialogVisible"
      :product="selectedProductCard"
    />

    <!-- Product detail dialog -->
    <ProductDetailDialog
      v-model="detailVisible"
      :product="detailProduct"
    />
  </div>
</template>

<style scoped>
.shop-layout {
  padding: 24px;
  height: 100%;
  overflow: auto;
  background: #f9fafb;
}
.content {
  max-width: 1100px;
  margin: 0 auto;
}

/* Banner */
.banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  margin-bottom: 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  border-radius: 12px;
  color: #fff;
}
.banner-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
}
.banner-sub {
  margin: 6px 0 0;
  font-size: 13px;
  opacity: 0.9;
}
.banner-cta {
  text-decoration: none;
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.search {
  max-width: 360px;
}
.sort {
  display: flex;
  align-items: center;
  gap: 6px;
}
.sort-label {
  font-size: 13px;
  color: #6b7280;
}

/* Grid */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}
.product-card {
  overflow: hidden;
  transition: transform 0.2s;
}
.product-card:hover {
  transform: translateY(-2px);
}
.img-wrap {
  position: relative;
  width: 100%;
  height: 180px;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  cursor: pointer;
}
.img {
  width: 100%;
  height: 100%;
}
.img-fallback {
  font-size: 48px;
}
.tag {
  position: absolute;
  top: 8px;
  right: 8px;
}
.info {
  padding: 12px;
}
.name {
  font-weight: 600;
  font-size: 15px;
  color: #1f2937;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}
.name:hover {
  color: #3b82f6;
}
.desc {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 39px;
}
.specs {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 6px;
  padding: 4px 6px;
  background: #f9fafb;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  margin-bottom: 8px;
}
.price {
  font-weight: 700;
  color: #dc2626;
  font-size: 17px;
}
.price-na {
  color: #6b7280;
  font-size: 13px;
}
.actions {
  display: flex;
  gap: 6px;
}
.actions .el-button {
  flex: 1;
}
.hint {
  margin-top: 28px;
  text-align: center;
  color: #6b7280;
  font-size: 13px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}
.link {
  color: #3b82f6;
  text-decoration: none;
}
.link:hover {
  text-decoration: underline;
}
</style>
