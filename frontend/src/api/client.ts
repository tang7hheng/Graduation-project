import axios from 'axios'

export const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

http.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const msg = error?.response?.data?.detail || error?.message || '请求失败'
    return Promise.reject(new Error(msg))
  },
)

// Type definitions shared across modules
export interface ChatSource {
  kind?: 'product' | 'doc' | null
  product_id?: string | null
  merchant_id?: string | null
  title: string
  snippet: string
  score: number
  price?: string
  page?: number | null
}

export interface SessionOut {
  id: string
  title: string
  summary?: string | null
  created_at: string
  updated_at: string
}

export interface MessageOut {
  id: number
  session_id: string
  role: 'user' | 'assistant'
  content: string
  sources_json: ChatSource[]
  product_cards_json: ProductCard[]
  created_at: string
}

export interface DocOut {
  id: string
  filename: string
  doc_type: string
  chunk_count: number
  status: string
  created_at: string
}

// === Merchant & Product ===
export interface MerchantOut {
  id: string
  name: string
  description?: string | null
  created_at: string
}

export interface ProductOut {
  id: string
  merchant_id: string
  name: string
  description: string
  price: string
  specs: string
  stock: number
  image_url: string
  status: string
  created_at: string
}

export interface ProductCreate {
  name: string
  description?: string
  price?: string
  specs?: string
  stock?: number
  image_url?: string
}

// === Product card (delivered via SSE / persisted on messages) ===
export interface ProductCard {
  id: string
  merchant_id: string
  name: string
  description: string
  price: string
  specs: string
  image_url: string
}

// === Order ===
export interface OrderItemOut {
  id: number
  product_id: string
  product_name: string
  price: string
  quantity: number
  image_url: string
}

export interface OrderOut {
  id: string
  session_id?: string | null
  merchant_id: string
  status: string
  total_amount: string
  remark: string
  created_at: string
  items: OrderItemOut[]
}

export interface OrderCreate {
  session_id?: string
  product_id: string
  quantity?: number
  remark?: string
}
