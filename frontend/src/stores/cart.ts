import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { checkoutCart } from '@/api/orders'
import { useChatStore } from '@/stores/chat'

export interface CartLine {
  product_id: string
  merchant_id: string
  name: string
  price: string
  image_url: string
  specs: string
  quantity: number
}

// add() 所需的结构化子集;ProductOut 和 ProductCard 都满足该结构
export interface CartProductInput {
  id: string
  merchant_id: string
  name: string
  price: string
  image_url: string
  specs: string
}

const STORAGE_KEY = 'rag-cs-cart'

function parsePrice(p: string): number {
  // 取第一个数字,避免 "199-299" 被解析成 199299
  const m = (p || '').match(/\d+(?:\.\d+)?/)
  return m ? parseFloat(m[0]) : 0
}

function load(): CartLine[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as CartLine[]) : []
  } catch {
    return []
  }
}

export const useCartStore = defineStore('cart', () => {
  const lines = ref<CartLine[]>(load())
  const drawerVisible = ref(false)
  const checkingOut = ref(false)

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(lines.value))
  }

  const count = computed(() =>
    lines.value.reduce((sum, l) => sum + l.quantity, 0),
  )

  const totalAmount = computed(() =>
    lines.value
      .reduce((sum, l) => sum + parsePrice(l.price) * l.quantity, 0)
      .toFixed(2),
  )

  function add(p: CartProductInput, qty = 1) {
    const existing = lines.value.find((l) => l.product_id === p.id)
    if (existing) {
      existing.quantity += qty
    } else {
      lines.value.push({
        product_id: p.id,
        merchant_id: p.merchant_id,
        name: p.name,
        price: p.price,
        image_url: p.image_url,
        specs: p.specs,
        quantity: qty,
      })
    }
    persist()
    ElMessage.success(`已加入购物车:${p.name}`)
  }

  function updateQty(productId: string, qty: number) {
    const line = lines.value.find((l) => l.product_id === productId)
    if (!line) return
    line.quantity = Math.max(1, qty)
    persist()
  }

  function remove(productId: string) {
    lines.value = lines.value.filter((l) => l.product_id !== productId)
    persist()
  }

  function clear() {
    lines.value = []
    persist()
  }

  function openDrawer() {
    drawerVisible.value = true
  }

  async function checkout(remark?: string): Promise<boolean> {
    if (lines.value.length === 0) return false
    const chat = useChatStore()
    checkingOut.value = true
    try {
      const items = lines.value.map((l) => ({
        product_id: l.product_id,
        quantity: l.quantity,
      }))
      const orders = await checkoutCart(items, chat.currentSessionId || undefined, remark)
      ElMessage.success(`下单成功!共生成 ${orders.length} 个订单`)
      clear()
      drawerVisible.value = false
      return true
    } catch (e: any) {
      ElMessage.error(e.message || '结算失败')
      return false
    } finally {
      checkingOut.value = false
    }
  }

  return {
    lines,
    drawerVisible,
    checkingOut,
    count,
    totalAmount,
    add,
    updateQty,
    remove,
    clear,
    openDrawer,
    checkout,
  }
})
