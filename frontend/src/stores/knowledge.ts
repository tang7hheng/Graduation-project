import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { DocOut } from '@/api/client'
import { http } from '@/api/client'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const documents = ref<DocOut[]>([])
  const uploading = ref<boolean>(false)
  const loading = ref<boolean>(false)

  async function fetchList() {
    loading.value = true
    try {
      const { data } = await http.get('/kb/documents')
      documents.value = (data as DocOut[]) || []
    } finally {
      loading.value = false
    }
  }

  async function upload(file: File) {
    uploading.value = true
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await http.post('/kb/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      })
      ElMessage.success(`上传成功:${data.filename}(${data.chunks} 块)`)
      await fetchList()
      return data
    } catch (e: any) {
      ElMessage.error(e.message || '上传失败')
      throw e
    } finally {
      uploading.value = false
    }
  }

  async function remove(id: string) {
    try {
      await http.delete(`/kb/documents/${id}`)
      ElMessage.success('已删除')
      documents.value = documents.value.filter((d) => d.id !== id)
    } catch (e: any) {
      ElMessage.error(e.message || '删除失败')
    }
  }

  async function rebuild() {
    try {
      const { data } = await http.post('/kb/rebuild', {}, { timeout: 300000 })
      ElMessage.success(`重建完成,共重新索引 ${data.reindexed} 个文档`)
      await fetchList()
    } catch (e: any) {
      ElMessage.error(e.message || '重建失败')
    }
  }

  return {
    documents,
    uploading,
    loading,
    fetchList,
    upload,
    remove,
    rebuild,
  }
})
