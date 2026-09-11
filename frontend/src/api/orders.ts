import { http } from './client'
import type { OrderOut, OrderCreate } from './client'

export async function createOrder(payload: OrderCreate): Promise<OrderOut> {
  const { data } = await http.post('/orders', payload)
  return data as OrderOut
}

export async function checkoutCart(
  items: { product_id: string; quantity: number }[],
  sessionId?: string,
  remark?: string,
): Promise<OrderOut[]> {
  const { data } = await http.post('/orders/checkout', {
    session_id: sessionId || null,
    items,
    remark: remark || '',
  })
  return data as OrderOut[]
}

export async function listOrders(sessionId?: string): Promise<OrderOut[]> {
  const { data } = await http.get('/orders', {
    params: sessionId ? { session_id: sessionId, page: 1, size: 100 } : { page: 1, size: 100 },
  })
  return (data.items as OrderOut[]) || []
}

export async function getOrder(orderId: string): Promise<OrderOut> {
  const { data } = await http.get(`/orders/${orderId}`)
  return data as OrderOut
}

export async function payOrder(orderId: string): Promise<OrderOut> {
  const { data } = await http.post(`/orders/${orderId}/pay`)
  return data as OrderOut
}

export async function cancelOrder(orderId: string): Promise<OrderOut> {
  const { data } = await http.post(`/orders/${orderId}/cancel`)
  return data as OrderOut
}
