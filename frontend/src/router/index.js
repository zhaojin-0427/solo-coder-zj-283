import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/materials',
    name: 'Materials',
    component: () => import('@/views/Materials.vue')
  },
  {
    path: '/projects',
    name: 'Projects',
    component: () => import('@/views/Projects.vue')
  },
  {
    path: '/projects/:id',
    name: 'ProjectDetail',
    component: () => import('@/views/ProjectDetail.vue')
  },
  {
    path: '/photos',
    name: 'ProcessPhotos',
    component: () => import('@/views/ProcessPhotos.vue')
  },
  {
    path: '/costs',
    name: 'Costs',
    component: () => import('@/views/Costs.vue')
  },
  {
    path: '/statistics',
    name: 'Statistics',
    component: () => import('@/views/Statistics.vue')
  },
  {
    path: '/orders',
    name: 'Orders',
    component: () => import('@/views/Orders.vue')
  },
  {
    path: '/orders/:id',
    name: 'OrderDetail',
    component: () => import('@/views/OrderDetail.vue')
  },
  {
    path: '/schedule',
    name: 'Schedule',
    component: () => import('@/views/Schedule.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
