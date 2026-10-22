import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/index.js'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => user.value?.username || '未登录')

  // Actions
  async function login(username, password) {
    const res = await api.post('/api/v1/user/login', { username, password })
    token.value = res.data.access_token
    localStorage.setItem('token', res.data.access_token)
    await fetchUser()
    return res
  }

  async function register(username, password, email) {
    const res = await api.post('/api/v1/user/register', { username, password, email })
    return res
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const res = await api.get('/api/v1/user/me')
      user.value = res.data
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, isLoggedIn, username, login, register, fetchUser, logout }
})
