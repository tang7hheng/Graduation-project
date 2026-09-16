import { createRouter, createWebHistory } from 'vue-router'
import { useRoleStore } from '@/stores/role'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    { path: '/merchant/login', name: 'merchantLogin', component: () => import('@/views/MerchantLoginView.vue') },
    { path: '/chat', name: 'chat', component: () => import('@/views/ChatView.vue'), meta: { roles: ['consumer'] } },
    { path: '/merchant', name: 'merchant', component: () => import('@/views/MerchantView.vue'), meta: { roles: ['merchant'] } },
    { path: '/products', name: 'products', component: () => import('@/views/ProductsView.vue'), meta: { roles: ['consumer'] } },
    { path: '/orders', name: 'orders', component: () => import('@/views/OrdersView.vue'), meta: { roles: ['consumer'] } },
  ],
})

router.beforeEach((to) => {
  const role = useRoleStore()
  const allowed = to.meta?.roles as string[] | undefined

  // Protected route: must have the right role
  if (allowed && !allowed.includes(role.role)) {
    // If not logged in at all, go to the right login page
    if (role.role === 'merchant') return '/merchant/login'
    return '/login'
  }
})

export default router
