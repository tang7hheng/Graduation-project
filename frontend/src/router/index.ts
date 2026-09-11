import { createRouter, createWebHistory } from 'vue-router'
import { useRoleStore } from '@/stores/role'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/products' },
    { path: '/chat', name: 'chat', component: () => import('@/views/ChatView.vue'), meta: { roles: ['consumer'] } },
    { path: '/knowledge', name: 'knowledge', component: () => import('@/views/KnowledgeView.vue'), meta: { roles: ['merchant'] } },
    { path: '/merchant', name: 'merchant', component: () => import('@/views/MerchantView.vue'), meta: { roles: ['merchant'] } },
    { path: '/products', name: 'products', component: () => import('@/views/ProductsView.vue'), meta: { roles: ['consumer'] } },
    { path: '/orders', name: 'orders', component: () => import('@/views/OrdersView.vue'), meta: { roles: ['consumer'] } },
  ],
})

router.beforeEach((to) => {
  const role = useRoleStore()
  const allowed = to.meta?.roles as string[] | undefined
  if (allowed && !allowed.includes(role.role)) {
    // Redirect to the default page for this role
    return role.isMerchant ? '/merchant' : '/products'
  }
})

export default router
