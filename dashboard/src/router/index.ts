import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/views/Dashboard.vue'),
    },
    {
      path: '/trade/open',
      component: () => import('@/views/OpenPosition.vue'),
    },
    {
      path: '/positions',
      component: () => import('@/views/Positions.vue'),
    },
    {
      path: '/trade/close',
      component: () => import('@/views/ClosePosition.vue'),
    },
    {
      path: '/statistics',
      component: () => import('@/views/Statistics.vue'),
    },
    {
      path: '/history',
      component: () => import('@/views/History.vue'),
    },
    {
      path: '/risk',
      component: () => import('@/views/RiskManagement.vue'),
    },
    {
      path: '/analysis',
      component: () => import('@/views/Analysis.vue'),
    },
    {
      path: '/settings',
      component: () => import('@/views/Settings.vue'),
    },
  ],
})

export default router
