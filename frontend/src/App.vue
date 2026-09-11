<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView, useRouter, useRoute } from 'vue-router'
import {
  ElContainer,
  ElHeader,
  ElMain,
  ElMenu,
  ElMenuItem,
  ElRadioGroup,
  ElRadioButton,
  ElBadge,
  ElIcon,
  ElButton,
} from 'element-plus'
import { ShoppingCart } from '@element-plus/icons-vue'
import { useRoleStore } from '@/stores/role'
import { useCartStore } from '@/stores/cart'
import CartDrawer from '@/components/shop/CartDrawer.vue'

const role = useRoleStore()
const cart = useCartStore()
const router = useRouter()
const route = useRoute()

onMounted(() => {
  if (role.isMerchant) void role.ensureMerchant()
})

function onRoleChange(val: string) {
  if (val === 'merchant') {
    role.switchToMerchant()
  } else {
    role.switchToConsumer()
  }
  // Route guard in router/index.ts will redirect if the current page is not allowed.
  // Force navigation so the guard runs even if already on a valid path.
  router.replace(route.path)
}

// Navigation menu items depend on role
function navItems() {
  if (role.isMerchant) {
    return [
      { index: '/merchant', label: '商品管理' },
      { index: '/knowledge', label: '知识库管理' },
    ]
  }
  return [
    { index: '/products', label: '商城' },
    { index: '/chat', label: '智能问答' },
    { index: '/orders', label: '我的订单' },
  ]
}
</script>

<template>
  <el-container class="app-layout">
    <el-header class="app-header">
      <div class="logo">智能客服 RAG</div>
      <el-menu
        mode="horizontal"
        router
        :default-active="route.path"
        class="nav-menu"
      >
        <el-menu-item
          v-for="item in navItems()"
          :key="item.index"
          :index="item.index"
        >
          {{ item.label }}
        </el-menu-item>
      </el-menu>
      <div class="right-area">
        <template v-if="role.isConsumer">
          <el-badge
            :value="cart.count"
            :hidden="cart.count === 0"
            class="cart-badge"
          >
            <el-button
              :icon="ShoppingCart"
              circle
              size="small"
              @click="cart.openDrawer()"
            />
          </el-badge>
        </template>
        <div class="role-switch">
          <span class="label">身份:</span>
          <el-radio-group
            :model-value="role.role"
            size="small"
            @change="onRoleChange"
          >
            <el-radio-button label="consumer">消费者</el-radio-button>
            <el-radio-button label="merchant">商户</el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </el-header>
    <el-main class="app-main">
      <RouterView />
    </el-main>

    <!-- Global shopping cart drawer (so it works on any page, not just shop) -->
    <CartDrawer />
  </el-container>
</template>

<style scoped>
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.app-header {
  display: flex;
  align-items: center;
  padding: 0 24px;
  background: #1f2937;
  color: #fff;
  height: 56px;
}
.logo {
  font-weight: 600;
  font-size: 18px;
  margin-right: 24px;
  flex-shrink: 0;
}
.nav-menu {
  background: transparent;
  border-bottom: none;
  flex: 1;
}
:deep(.nav-menu .el-menu-item) {
  color: #d1d5db;
  border-bottom: none;
}
:deep(.nav-menu .el-menu-item.is-active) {
  color: #fff;
  background: #374151;
  border-bottom: 2px solid #60a5fa;
}
.right-area {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}
.cart-badge {
  margin-right: 4px;
}
.role-switch {
  display: flex;
  align-items: center;
  gap: 8px;
}
.role-switch .label {
  font-size: 12px;
  color: #9ca3af;
}
.app-main {
  flex: 1;
  padding: 0;
  overflow: hidden;
  background: #f3f4f6;
}
</style>
