import { http } from './client'
import type { MerchantOut, ProductOut, ProductCreate } from './client'

export async function createMerchant(name: string, description = ''): Promise<MerchantOut> {
  const { data } = await http.post('/merchants', { name, description })
  return data as MerchantOut
}

export async function listMerchants(): Promise<MerchantOut[]> {
  const { data } = await http.get('/merchants')
  return data as MerchantOut[]
}

export async function listMerchantProducts(merchantId: string): Promise<ProductOut[]> {
  const { data } = await http.get(`/merchants/${merchantId}/products`)
  return data as ProductOut[]
}

export async function createProduct(
  merchantId: string,
  payload: ProductCreate,
): Promise<ProductOut> {
  const { data } = await http.post(`/merchants/${merchantId}/products`, payload)
  return data as ProductOut
}

export async function listAllProducts(): Promise<ProductOut[]> {
  const { data } = await http.get('/products')
  return data as ProductOut[]
}

export async function deleteProduct(productId: string): Promise<void> {
  await http.delete(`/products/${productId}`)
}
