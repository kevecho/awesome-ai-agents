import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
  },
  {
    path: '/consult/:id',
    name: 'Consult',
    component: () => import('../views/Consult.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: () => import('../views/Knowledge.vue'),
  },
  {
    path: '/records',
    name: 'Records',
    component: () => import('../views/Records.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
