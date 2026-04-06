<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { registerApi } from '@/api/auth'

const router = useRouter()
const authStore = useAuthStore()

const mode = ref<'login' | 'register'>('login')
const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const loading = ref(false)
const errorMsg = ref('')

const isLogin = computed(() => mode.value === 'login')

const canSubmit = computed(() => {
  if (!username.value || !password.value) return false
  if (!isLogin.value && password.value !== confirmPassword.value) return false
  return true
})

async function submit() {
  errorMsg.value = ''
  loading.value = true
  try {
    if (isLogin.value) {
      await authStore.login(username.value, password.value)
    } else {
      const res = await registerApi({ username: username.value, email: email.value, password: password.value })
      authStore.setTokens(res.data.access, res.data.refresh)
      authStore.setUser(res.data.username, res.data.email)
    }
    router.replace('/dashboard')
  } catch (e: unknown) {
    const err = e as { response?: { data?: Record<string, unknown> } }
    const data = err?.response?.data
    if (data) {
      const msgs = Object.values(data).flat()
      errorMsg.value = (msgs[0] as string) || '操作失敗，請再試一次'
    } else {
      errorMsg.value = '無法連線到伺服器'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-4 relative overflow-hidden"
       style="background: var(--bg-base)">

    <!-- Aurora background -->
    <div class="aurora-bg" aria-hidden="true">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
    </div>

    <!-- Card -->
    <div class="relative z-10 w-full max-w-md">
      <div class="glass rounded-2xl p-8 shadow-2xl border" style="border-color: var(--border-soft)">

        <!-- Logo -->
        <div class="flex flex-col items-center mb-8">
          <div class="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
               style="background: var(--bg-elevated); box-shadow: 0 0 24px var(--accent-glow)">
            <i class="fa-solid fa-paw text-3xl" style="color: var(--accent)"></i>
          </div>
          <h1 class="text-2xl font-bold font-display" style="color: var(--text-primary)">PerPetsStore ERP</h1>
          <p class="text-sm mt-1" style="color: var(--text-muted)">
            {{ isLogin ? '歡迎回來，請登入您的帳號' : '建立新帳號' }}
          </p>
        </div>

        <!-- Mode toggle -->
        <div class="flex bg-slate-100 dark:bg-slate-800 rounded-xl p-1 mb-6">
          <button
            class="flex-1 py-2 text-sm font-medium rounded-lg transition-all duration-200"
            :class="isLogin ? 'bg-white dark:bg-slate-700 text-purple-600 dark:text-purple-400 shadow-sm' : 'text-slate-500 dark:text-slate-400'"
            @click="mode = 'login'; errorMsg = ''"
          >登入</button>
          <button
            class="flex-1 py-2 text-sm font-medium rounded-lg transition-all duration-200"
            :class="!isLogin ? 'bg-white dark:bg-slate-700 text-purple-600 dark:text-purple-400 shadow-sm' : 'text-slate-500 dark:text-slate-400'"
            @click="mode = 'register'; errorMsg = ''"
          >註冊</button>
        </div>

        <!-- Form -->
        <form @submit.prevent="submit" class="space-y-4">

          <!-- Username -->
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary)">帳號</label>
            <div class="relative">
              <i class="fa-solid fa-user absolute left-3.5 top-1/2 -translate-y-1/2 text-sm" style="color: var(--text-muted)"></i>
              <input
                v-model="username"
                type="text"
                autocomplete="username"
                placeholder="輸入帳號"
                class="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm transition-all outline-none border focus:ring-2"
                style="background: var(--bg-elevated); border-color: var(--border-soft); color: var(--text-primary); --tw-ring-color: var(--accent-glow)"
              />
            </div>
          </div>

          <!-- Email (register only) -->
          <Transition name="fade">
            <div v-if="!isLogin">
              <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary)">Email（選填）</label>
              <div class="relative">
                <i class="fa-solid fa-envelope absolute left-3.5 top-1/2 -translate-y-1/2 text-sm" style="color: var(--text-muted)"></i>
                <input
                  v-model="email"
                  type="email"
                  autocomplete="email"
                  placeholder="example@email.com"
                  class="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm transition-all outline-none border focus:ring-2"
                  style="background: var(--bg-elevated); border-color: var(--border-soft); color: var(--text-primary)"
                />
              </div>
            </div>
          </Transition>

          <!-- Password -->
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary)">密碼</label>
            <div class="relative">
              <i class="fa-solid fa-lock absolute left-3.5 top-1/2 -translate-y-1/2 text-sm" style="color: var(--text-muted)"></i>
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="輸入密碼"
                class="w-full pl-10 pr-10 py-2.5 rounded-xl text-sm transition-all outline-none border focus:ring-2"
                style="background: var(--bg-elevated); border-color: var(--border-soft); color: var(--text-primary)"
              />
              <button type="button" class="absolute right-3.5 top-1/2 -translate-y-1/2 text-sm" style="color: var(--text-muted)" @click="showPassword = !showPassword">
                <i :class="showPassword ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye'"></i>
              </button>
            </div>
          </div>

          <!-- Confirm Password (register only) -->
          <Transition name="fade">
            <div v-if="!isLogin">
              <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary)">確認密碼</label>
              <div class="relative">
                <i class="fa-solid fa-lock absolute left-3.5 top-1/2 -translate-y-1/2 text-sm" style="color: var(--text-muted)"></i>
                <input
                  v-model="confirmPassword"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  placeholder="再次輸入密碼"
                  class="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm transition-all outline-none border focus:ring-2"
                  :class="confirmPassword && password !== confirmPassword ? 'border-red-400' : ''"
                  style="background: var(--bg-elevated); border-color: var(--border-soft); color: var(--text-primary)"
                />
              </div>
              <p v-if="confirmPassword && password !== confirmPassword" class="text-xs text-red-500 mt-1">密碼不一致</p>
            </div>
          </Transition>

          <!-- Error -->
          <Transition name="fade">
            <div v-if="errorMsg" class="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700">
              <i class="fa-solid fa-circle-exclamation text-red-500 shrink-0 text-sm"></i>
              <span class="text-sm text-red-600 dark:text-red-400">{{ errorMsg }}</span>
            </div>
          </Transition>

          <!-- Submit -->
          <button
            type="submit"
            :disabled="!canSubmit || loading"
            class="w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 dark:hover:from-[#B8936A] dark:hover:to-[#8F6A3C]"
          >
            <i v-if="loading" class="fa-solid fa-spinner fa-spin mr-2"></i>
            {{ isLogin ? '登入' : '建立帳號' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s, transform 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
