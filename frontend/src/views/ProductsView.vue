<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElCard, ElEmpty, ElTag, ElInput, ElButton, ElImage } from 'element-plus'
import { Search, ShoppingCart, Plus, ChatDotRound } from '@element-plus/icons-vue'
import type { ProductOut } from '@/api/client'
import { listAllProducts } from '@/api/products'
import { useCartStore } from '@/stores/cart'
import { useChatStore } from '@/stores/chat'
import OrderDialog from '@/components/chat/OrderDialog.vue'
import ProductDetailDialog from '@/components/shop/ProductDetailDialog.vue'

const router = useRouter()
const cart = useCartStore()
const chatStore = useChatStore()
const products = ref<ProductOut[]>([])
const loading = ref(false)
const keyword = ref('')
const sortMode = ref<'default' | 'price-asc' | 'price-desc'>('default')
const orderDialogVisible = ref(false)
const selectedProductCard = ref<any>(null)
const detailVisible = ref(false)
const detailProduct = ref<ProductOut | null>(null)

onMounted(async () => {
  loading.value = true
  try { products.value = await listAllProducts() }
  finally { loading.value = false }
})

function parsePrice(p: string): number {
  // 取第一个数字,避免 "199-299" 被解析成 199299
  const m = (p || '').match(/\d+(?:\.\d+)?/)
  return m ? parseFloat(m[0]) : 0
}

const filtered = computed(() => {
  let list = products.value
  const k = keyword.value.trim().toLowerCase()
  if (k) {
    list = list.filter(p =>
      p.name.toLowerCase().includes(k) ||
      p.description.toLowerCase().includes(k) ||
      p.specs.toLowerCase().includes(k)
    )
  }
  if (sortMode.value === 'price-asc') list = [...list].sort((a, b) => parsePrice(a.price) - parsePrice(b.price))
  else if (sortMode.value === 'price-desc') list = [...list].sort((a, b) => parsePrice(b.price) - parsePrice(a.price))
  return list
})

function addToCart(p: ProductOut) { cart.add(p, 1) }

function buyNow(p: ProductOut) {
  selectedProductCard.value = {
    id: p.id, merchant_id: p.merchant_id, name: p.name,
    description: p.description, price: p.price, specs: p.specs, image_url: p.image_url,
  }
  orderDialogVisible.value = true
}

function openDetail(p: ProductOut) { detailProduct.value = p; detailVisible.value = true }

function askAIAbout(p: ProductOut) {
  chatStore.pendingQuery = `帮我看看这个商品:${p.name},价格¥${p.price},${p.description || ''}`
  router.push('/chat')
}
</script>

<template>
  <div class="shop-layout">
    <div class="content">
      <!-- Banner -->
      <div class="banner">
        <div class="banner-text">
          <h1 class="banner-title">智选商城</h1>
          <p class="banner-sub">品质好物 · 智能推荐 · 极速下单</p>
        </div>
        <router-link to="/chat" class="banner-cta">
          <el-button type="primary" round size="large">咨询智能导购</el-button>
        </router-link>
      </div>

      <!-- Toolbar -->
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索商品名称 / 描述 / 规格" :prefix-icon="Search" clearable class="search" />
        <div class="sort">
          <span class="sort-label">排序:</span>
          <el-button size="small" :type="sortMode === 'default' ? 'primary' : 'default'" @click="sortMode = 'default'">综合</el-button>
          <el-button size="small" :type="sortMode === 'price-asc' ? 'primary' : 'default'" @click="sortMode = 'price-asc'">价格↑</el-button>
          <el-button size="small" :type="sortMode === 'price-desc' ? 'primary' : 'default'" @click="sortMode = 'price-desc'">价格↓</el-button>
        </div>
      </div>

      <!-- Grid -->
      <el-empty v-if="!loading && filtered.length === 0" description="暂无商品" />
      <div class="grid" v-loading="loading">
        <el-card v-for="p in filtered" :key="p.id" class="product-card" shadow="hover" :body-style="{ padding: '0' }">
          <div class="img-wrap" @click="openDetail(p)">
            <el-image v-if="p.image_url" :src="p.image_url" fit="cover" class="img">
              <template #error><div class="img-fallback">购</div></template>
            </el-image>
            <div v-else class="img-fallback">购</div>
            <el-tag class="tag" size="small" :type="p.stock > 0 ? 'success' : 'danger'" effect="light">
              {{ p.stock > 0 ? '库存充足' : '缺货' }}
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
              <el-button size="small" :icon="Plus" @click="addToCart(p)">购物车</el-button>
              <el-button size="small" :icon="ChatDotRound" @click="askAIAbout(p)">问AI</el-button>
              <el-button type="primary" size="small" :icon="ShoppingCart" @click="buyNow(p)">购买</el-button>
            </div>
          </div>
        </el-card>
      </div>

      <div class="hint">
        没找到心仪商品?前往 <router-link to="/chat" class="link">智能导购</router-link> 告诉我你的需求,我来帮你找。
      </div>
    </div>

    <OrderDialog v-model="orderDialogVisible" :product="selectedProductCard" />
    <ProductDetailDialog v-model="detailVisible" :product="detailProduct" />
  </div>
</template>

<style scoped>
.shop-layout {
  padding: 24px;
  height: 100%;
  overflow: auto;
  background: var(--bg-base);
}
.content { max-width: 1100px; margin: 0 auto; }

.banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32px 36px;
  margin-bottom: 20px;
  background: var(--accent-primary-light);
  border-radius: var(--radius-lg);
  color: var(--text-primary);
  border: 1px solid #a5b4fc;
}
.banner-title { margin: 0; font-size: 26px; font-weight: 800; letter-spacing: -0.5px; color: var(--accent-primary-dark); }
.banner-sub { margin: 8px 0 0; font-size: 14px; color: var(--text-secondary); }
.banner-cta { text-decoration: none; }
.banner-cta .el-button {
  --el-button-bg-color: var(--accent-primary);
  --el-button-border-color: var(--accent-primary);
  --el-button-hover-bg-color: var(--accent-primary-dark);
  --el-button-hover-border-color: var(--accent-primary-dark);
  --el-button-text-color: #fff;
  font-weight: 600;
}

.toolbar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; margin-bottom: 20px; flex-wrap: wrap;
}
.search { max-width: 360px; }
.search :deep(.el-input__wrapper) {
  border-radius: var(--radius-sm); background: var(--bg-surface); box-shadow: 0 0 0 1px var(--border-base);
}
.search :deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 1px var(--accent-primary); }
.sort { display: flex; align-items: center; gap: 6px; }
.sort-label { font-size: 13px; color: var(--text-secondary); font-weight: 600; }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.product-card {
  overflow: hidden;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-base);
  transition: transform 0.2s, box-shadow 0.2s;
}
.product-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); }
.img-wrap {
  position: relative; width: 100%; height: 180px;
  background: var(--bg-muted);
  display: flex; align-items: center; justify-content: center; overflow: hidden; cursor: pointer;
}
.img { width: 100%; height: 100%; }
.img-fallback {
  font-weight: 800; font-size: 48px; color: var(--text-tertiary);
}
.tag { position: absolute; top: 8px; right: 8px; }
.info { padding: 14px; }
.name {
  font-weight: 700; font-size: 15px; color: var(--text-primary);
  margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  cursor: pointer; transition: color 0.15s;
}
.name:hover { color: var(--accent-primary); }
.desc {
  font-size: 13px; color: var(--text-secondary); line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; min-height: 39px;
}
.specs {
  font-size: 12px; color: var(--text-tertiary); margin-top: 6px;
  padding: 4px 8px; background: var(--bg-muted); border-radius: var(--radius-sm);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.footer { display: flex; align-items: center; justify-content: space-between; margin-top: 10px; margin-bottom: 8px; }
.price { font-weight: 800; color: var(--accent-price); font-size: 18px; }
.price-na { color: var(--text-tertiary); font-size: 13px; }
.actions { display: flex; gap: 6px; }
.actions .el-button { flex: 1; }
.hint {
  margin-top: 28px; text-align: center; color: var(--text-secondary);
  font-size: 13px; padding: 16px; background: var(--bg-surface);
  border-radius: var(--radius-sm); border: 1px solid var(--border-base);
}
.link { color: var(--accent-primary); text-decoration: none; font-weight: 600; }
.link:hover { text-decoration: underline; }
</style>
