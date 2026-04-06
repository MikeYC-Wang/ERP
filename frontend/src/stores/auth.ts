import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, getMeApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const username = ref<string>(localStorage.getItem('username') ?? '')
  const email = ref<string>(localStorage.getItem('email') ?? '')

  const isAuthenticated = computed(() => !!accessToken.value)

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function setUser(name: string, userEmail: string) {
    username.value = name
    email.value = userEmail
    localStorage.setItem('username', name)
    localStorage.setItem('email', userEmail)
  }

  async function login(user: string, password: string) {
    const res = await loginApi({ username: user, password })
    setTokens(res.data.access, res.data.refresh)
    await fetchMe()
  }

  async function fetchMe() {
    try {
      const res = await getMeApi()
      setUser(res.data.username, res.data.email)
    } catch {
      // ignore
    }
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    username.value = ''
    email.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('username')
    localStorage.removeItem('email')
  }

  return { accessToken, refreshToken, username, email, isAuthenticated, login, logout, fetchMe, setTokens, setUser }
})
