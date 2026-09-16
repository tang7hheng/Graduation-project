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
        title='上架商品时请填写「功能介绍与使用说明」,包含功能、用法、售后政策等。这些内容构成商品知识库,AI客服据此为用户介绍和推荐。'
      />
      <ProductForm />
      <ProductTable />
    </div>
  </div>
</template>

<style scoped>
.merchant-layout { padding: 24px; height: 100%; overflow: auto; background: var(--bg-base); }
.content { max-width: 960px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px; }
</style>
