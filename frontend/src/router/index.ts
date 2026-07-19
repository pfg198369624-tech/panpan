import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'Home', component: () => import('@/views/Home.vue') },
    { path: '/workflow', name: 'Workflow', component: () => import('@/views/Workflow.vue') },
    { path: '/reviews', name: 'Reviews', component: () => import('@/views/Reviews.vue') },
    { path: '/analysis', name: 'Analysis', component: () => import('@/views/Analysis.vue') },
    { path: '/prd', name: 'PRD', component: () => import('@/views/PRD.vue') },
    { path: '/test-cases', name: 'TestCases', component: () => import('@/views/TestCases.vue') },
    { path: '/data-source', name: 'DataSource', component: () => import('@/views/DataSource.vue') },
  ],
})

export default router
