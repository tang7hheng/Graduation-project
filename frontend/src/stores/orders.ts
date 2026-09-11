import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { OrderOut, OrderCreate } from '@/api/client'
import {
  createOrder,
  listOrders,
  payOrder,
  cancelOrder,
} from '@/api/orders'

export const useOrdersStore = defineStore('orders', () => {
  const orders = ref<OrderOut[]>([])
  const loading = ref(false)
  const placing = ref(false)

  async function fetchList(sessionId?: string) {
    loading.value = true
    try {
      orders.value = await listOrders(sessionId)
    } finally {
      loading.value = false
    }
  }

  async function placeOrder(payload: OrderCreate): Promise<OrderOut | null> {
    placing.value = true
    try {
      const o = await createOrder(payload)
      ElMessage.success(`下单成功!订单号:${o.id.slice(0, 8)}`)
      orders.value.unshift(o)
      return o
    } catch (e: any) {
      ElMessage.error(e.message || '下单失败')
      return null
    } finally {
      placing.value = false
    }
  }

  async function pay(orderId: string) {
    try {
      const o = await payOrder(orderId)
      ElMessage.success('支付成功(模拟)')
      const idx = orders.value.findIndex((x) => x.id === orderId)
      if (idx >= 0) orders.value[idx] = o
    } catch (e: any) {
      ElMessage.error(e.message || '支付失败')
    }
  }

  async function cancel(orderId: string) {
    try {
      const o = await cancelOrder(orderId)
      ElMessage.success('订单已取消')
      const idx = orders.value.findIndex((x) => x.id === orderId)
      if (idx >= 0) orders.value[idx] = o
    } catch (e: any) {
      ElMessage.error(e.message || '取消失败')
    }
  }

  return {
    orders,
    loading,
    placing,
    fetchList,
    placeOrder,
    pay,
    cancel,
  }
})
