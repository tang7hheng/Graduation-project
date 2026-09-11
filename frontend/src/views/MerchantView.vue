<script setup lang="ts">
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { ElAlert } from 'element-plus'
import ProductForm from '@/components/merchant/ProductForm.vue'
import ProductTable from '@/components/merchant/ProductTable.vue'
import { useMerchantProductsStore } from '@/stores/merchantProducts'
import { useRoleStore } from '@/stores/role'

const store = useMerchantProductsStore()
const role = useRoleStore()
const { currentMerchant } = storeToRefs(role)

onMounted(async () => {
  await role.ensureMerchant()
  await store.fetchList()
})
</script>

<template>
  <div class="merchant-layout">
    <div class="content">
      <el-alert
        type="success"
        :closable="false"
        show-icon
        :title="`当前商户:${currentMerchant?.name || '初始化中...'}(仅本浏览器会话使用,无登录认证)`"
      />
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="上架的商品会自动入索引,消费者提问时客服会基于这些商品信息回答。"
      />
      <ProductForm />
      <ProductTable />
    </div>
  </div>
</template>

<style scoped>
.merchant-layout {
  padding: 24px;
  height: 100%;
  overflow: auto;
}
.content {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
