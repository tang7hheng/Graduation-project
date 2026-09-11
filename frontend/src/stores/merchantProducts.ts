import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { ProductOut, ProductCreate } from '@/api/client'
import {
  listMerchantProducts,
  createProduct,
  deleteProduct,
} from '@/api/products'
import { useRoleStore } from '@/stores/role'

export const useMerchantProductsStore = defineStore('merchantProducts', () => {
  const products = ref<ProductOut[]>([])
  const loading = ref(false)
  const submitting = ref(false)

  async function fetchList() {
    const role = useRoleStore()
    if (!role.currentMerchant) {
      await role.ensureMerchant()
    }
    if (!role.currentMerchant) return
    loading.value = true
    try {
      products.value = await listMerchantProducts(role.currentMerchant.id)
    } finally {
      loading.value = false
    }
  }

  async function add(payload: ProductCreate) {
    const role = useRoleStore()
    if (!role.currentMerchant) {
      await role.ensureMerchant()
    }
    if (!role.currentMerchant) throw new Error('商户未初始化')
    submitting.value = true
    try {
      const p = await createProduct(role.currentMerchant.id, payload)
      ElMessage.success(`商品已上架:${p.name}`)
      products.value.unshift(p)
      return p
    } catch (e: any) {
      ElMessage.error(e.message || '上架失败')
      throw e
    } finally {
      submitting.value = false
    }
  }

  async function remove(id: string) {
    try {
      await deleteProduct(id)
      ElMessage.success('已下架')
      products.value = products.value.filter((p) => p.id !== id)
    } catch (e: any) {
      ElMessage.error(e.message || '下架失败')
    }
  }

  return {
    products,
    loading,
    submitting,
    fetchList,
    add,
    remove,
  }
})
