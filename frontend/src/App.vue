<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView, useRouter, useRoute } from 'vue-router'
import {
  ElContainer,
  ElHeader,
  ElMain,
  ElMenu,
  ElMenuItem,
  ElBadge,
  ElButton,
} from 'element-plus'
import { ShoppingCart, SwitchButton } from '@element-plus/icons-vue'
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

function logout() {
  role.switchToConsumer()
  router.replace('/login')
}

function navItems() {
  if (role.isMerchant) {
    return [
      { index: '/merchant', label: '商品管理' },
      { index: '/knowledge', label: '知识库' },
    ]
  }
  return [
    { index: '/products', label: '商城' },
    { index: '/chat', label: '智能导购' },
    { index: '/orders', label: '我的订单' },
  ]
}
</script>

<template>
  <el-container class="app-layout">
    <el-header class="app-header">
      <div class="logo" @click="router.push(role.isMerchant ? '/merchant' : '/products')">
        <div class="logo-mark">购</div>
        <span class="logo-text">智选商城</span>
      </div>
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
              class="cart-btn"
              @click="cart.openDrawer()"
            />
          </el-badge>
        </template>
        <el-button
          :icon="SwitchButton"
          size="small"
          text
          class="logout-btn"
          @click="logout"
        >
          退出
        </el-button>
      </div>
    </el-header>
    <el-main class="app-main">
      <RouterView />
    </el-main>

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
  padding: 0 32px;
  background: var(--bg-surface);
  height: 60px;
  border-bottom: 1px solid var(--border-base);
  box-shadow: var(--shadow-sm);
  position: relative;
  z-index: 10;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-right: 32px;
  flex-shrink: 0;
  cursor: pointer;
}
.logo-mark {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: var(--accent-primary);
  color: #fff;
  font-weight: 800;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(79, 70, 229, 0.2);
}
.logo-text {
  font-weight: 800;
  font-size: 18px;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}
.nav-menu {
  background: transparent;
  border-bottom: none;
  flex: 1;
}
:deep(.nav-menu .el-menu-item) {
  color: var(--text-secondary);
  border-bottom: none;
  font-size: 14px;
  font-weight: 600;
  transition: color 0.15s;
}
:deep(.nav-menu .el-menu-item:hover) {
  color: var(--accent-primary);
  background: transparent;
}
:deep(.nav-menu .el-menu-item.is-active) {
  color: var(--accent-primary);
  background: transparent;
  border-bottom: 2px solid var(--accent-primary);
}
.right-area {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}
.cart-badge { margin-right: 4px; }
.cart-btn {
  border-color: var(--border-base) !important;
  color: var(--text-secondary) !important;
  background: var(--bg-surface) !important;
}
.cart-btn:hover {
  border-color: var(--accent-primary) !important;
  color: var(--accent-primary) !important;
}
.logout-btn {
  color: var(--text-tertiary) !important;
}
.logout-btn:hover {
  color: var(--accent-primary) !important;
}
.app-main {
  flex: 1;
  padding: 0;
  overflow: hidden;
  background: var(--bg-base);
}
</style>
