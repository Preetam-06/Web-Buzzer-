import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/admin' },
  { path: '/admin', component: () => import('../views/AdminView.vue') },
  { path: '/join/:code', component: () => import('../views/JoinView.vue'), props:true },
  { path: '/play', component: () => import('../views/PlayView.vue') },
  { path: '/display/:code', component: () => import('../views/DisplayView.vue'), props:true },
  { path: '/:pathMatch(.*)*', redirect: '/admin' },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})
export default router
