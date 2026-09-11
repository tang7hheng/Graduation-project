import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { MerchantOut } from '@/api/client'
import { http } from '@/api/client'

export type Role = 'consumer' | 'merchant'

const STORAGE_KEY = 'rag-cs-role'
const MERCHANT_KEY = 'rag-cs-merchant-id'

export const useRoleStore = defineStore('role', () => {
  const stored = localStorage.getItem(STORAGE_KEY)
  const role = ref<Role>(stored === 'merchant' || stored === 'consumer' ? stored : 'consumer')
  const currentMerchant = ref<MerchantOut | null>(null)

  const isMerchant = computed(() => role.value === 'merchant')
  const isConsumer = computed(() => role.value === 'consumer')

  function setRole(r: Role) {
    role.value = r
    localStorage.setItem(STORAGE_KEY, r)
  }

  async function ensureMerchant(): Promise<MerchantOut> {
    if (currentMerchant.value) return currentMerchant.value

    // Try to restore from localStorage
    const storedId = localStorage.getItem(MERCHANT_KEY)
    if (storedId) {
      try {
        const { data } = await http.get(`/merchants/${storedId}`)
        currentMerchant.value = data as MerchantOut
        return currentMerchant.value
      } catch {
        // merchant no longer exists, fall through to create
      }
    }

    // Create a new merchant for this browser session
    const { data } = await http.post('/merchants', {
      name: `商户-${Math.random().toString(36).slice(2, 8)}`,
      description: '',
    })
    currentMerchant.value = data as MerchantOut
    localStorage.setItem(MERCHANT_KEY, currentMerchant.value.id)
    return currentMerchant.value
  }

  function switchToMerchant() {
    setRole('merchant')
    void ensureMerchant()
  }

  function switchToConsumer() {
    setRole('consumer')
  }

  return {
    role,
    currentMerchant,
    isMerchant,
    isConsumer,
    setRole,
    ensureMerchant,
    switchToMerchant,
    switchToConsumer,
  }
})
