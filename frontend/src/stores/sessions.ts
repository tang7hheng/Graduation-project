import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SessionOut } from '@/api/client'
import { http } from '@/api/client'

export const useSessionsStore = defineStore('sessions', () => {
  const list = ref<SessionOut[]>([])
  const currentId = ref<string>('')
  const loading = ref<boolean>(false)

  const currentSession = computed(() =>
    list.value.find((s) => s.id === currentId.value),
  )

  async function fetchList() {
    loading.value = true
    try {
      const { data } = await http.get('/sessions', { params: { page: 1, size: 100 } })
      list.value = (data.items as SessionOut[]) || []
    } finally {
      loading.value = false
    }
  }

  async function create(title?: string) {
    const { data } = await http.post('/sessions', { title })
    const s = data as SessionOut
    list.value.unshift(s)
    currentId.value = s.id
    return s
  }

  async function select(id: string) {
    currentId.value = id
  }

  async function remove(id: string) {
    await http.delete(`/sessions/${id}`)
    list.value = list.value.filter((s) => s.id !== id)
    if (currentId.value === id) currentId.value = ''
  }

  return {
    list,
    currentId,
    currentSession,
    loading,
    fetchList,
    create,
    select,
    remove,
  }
})
