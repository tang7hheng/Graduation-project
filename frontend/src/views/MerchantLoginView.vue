<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useRoleStore } from '@/stores/role'
import { ElButton } from 'element-plus'
import { Goods, Setting } from '@element-plus/icons-vue'

const role = useRoleStore()
const router = useRouter()

function enter() {
  role.switchToMerchant()
  router.replace('/merchant')
}

function goConsumer() {
  router.replace('/login')
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo-mark">商</div>
      <h1 class="title">商户后台</h1>
      <p class="subtitle">商户入口</p>
      <div class="features">
        <div class="feature-item">
          <el-icon :size="24"><Goods /></el-icon>
          <span>上架商品 · 编辑信息 · 管理库存</span>
        </div>
        <div class="feature-item">
          <el-icon :size="24"><Setting /></el-icon>
          <span>商品知识库 · AI 客服依据</span>
        </div>
      </div>
      <el-button type="primary" size="large" class="enter-btn" @click="enter">
        进入管理后台
      </el-button>
      <el-button text size="small" class="consumer-link" @click="goConsumer">
        ← 我是消费者
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eef2ff 0%, #faf5ff 100%);
}
.login-card {
  background: var(--bg-surface);
  border-radius: 16px;
  padding: 48px 56px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  min-width: 360px;
}
.logo-mark {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: var(--accent-primary);
  color: #fff;
  font-weight: 800;
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
}
.title {
  font-size: 28px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0;
}
.subtitle {
  font-size: 14px;
  color: var(--text-tertiary);
  margin: 0;
}
.features {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 16px 0 8px;
}
.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-secondary);
}
.enter-btn {
  width: 100%;
  margin: 0 !important;
}
.consumer-link {
  margin-top: 8px !important;
  color: var(--text-tertiary) !important;
}
.consumer-link:hover {
  color: var(--accent-primary) !important;
}
</style>
