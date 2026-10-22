<template>
  <div class="login-page">
    <!-- Left: Branding & Illustration -->
    <div class="login-brand">
      <div class="brand-bg">
        <div class="wave wave-1"></div>
        <div class="wave wave-2"></div>
        <div class="wave wave-3"></div>
      </div>
      <div class="brand-content">
        <div class="brand-logo">
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="32" cy="32" r="30" fill="white" fill-opacity="0.1" stroke="white" stroke-width="2"/>
            <path d="M32 18C32.8 18 33.5 18.7 33.5 19.5V28.5H42.5C43.3 28.5 44 29.2 44 30V34C44 34.8 43.3 35.5 42.5 35.5H33.5V44.5C33.5 45.3 32.8 46 32 46H28C27.2 46 26.5 45.3 26.5 44.5V35.5H17.5C16.7 35.5 16 34.8 16 34V30C16 29.2 16.7 28.5 17.5 28.5H26.5V19.5C26.5 18.7 27.2 18 28 18H32Z" fill="white" fill-opacity="0.8"/>
            <circle cx="18" cy="18" r="2.5" fill="white" fill-opacity="0.25"/>
            <circle cx="46" cy="18" r="2.5" fill="white" fill-opacity="0.25"/>
            <circle cx="18" cy="46" r="2.5" fill="white" fill-opacity="0.25"/>
            <circle cx="46" cy="46" r="2.5" fill="white" fill-opacity="0.25"/>
            <path d="M20 20L25 25" stroke="white" stroke-width="1" stroke-opacity="0.15" stroke-linecap="round"/>
            <path d="M44 20L39 25" stroke="white" stroke-width="1" stroke-opacity="0.15" stroke-linecap="round"/>
            <path d="M20 44L25 39" stroke="white" stroke-width="1" stroke-opacity="0.15" stroke-linecap="round"/>
            <path d="M44 44L39 39" stroke="white" stroke-width="1" stroke-opacity="0.15" stroke-linecap="round"/>
          </svg>
        </div>
        <h1 class="brand-title">AI 智能问诊系统</h1>
        <p class="brand-subtitle">基于 LLM 大模型 + Agent 架构 + RAG 检索增强</p>
        <div class="brand-features">
          <div class="brand-feature">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM10 18C5.59 18 2 14.41 2 10C2 5.59 5.59 2 10 2C14.41 2 18 5.59 18 10C18 14.41 14.41 18 10 18Z" fill="white"/>
              <path d="M14.59 5.58L8 12.17L5.41 9.59L4 11L8 15L16 7L14.59 5.58Z" fill="white"/>
            </svg>
            <span>AI 智能症状分析</span>
          </div>
          <div class="brand-feature">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM10 18C5.59 18 2 14.41 2 10C2 5.59 5.59 2 10 2C14.41 2 18 5.59 18 10C18 14.41 14.41 18 10 18Z" fill="white"/>
              <path d="M14.59 5.58L8 12.17L5.41 9.59L4 11L8 15L16 7L14.59 5.58Z" fill="white"/>
            </svg>
            <span>海量医学知识库</span>
          </div>
          <div class="brand-feature">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM10 18C5.59 18 2 14.41 2 10C2 5.59 5.59 2 10 2C14.41 2 18 5.59 18 10C18 14.41 14.41 18 10 18Z" fill="white"/>
              <path d="M14.59 5.58L8 12.17L5.41 9.59L4 11L8 15L16 7L14.59 5.58Z" fill="white"/>
            </svg>
            <span>实时交互咨询</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Right: Login Form -->
    <div class="login-form-panel">
      <div class="login-card">
        <div class="login-card-header">
          <div class="login-card-logo">
            <svg width="40" height="40" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="32" cy="32" r="30" fill="url(#brandG)" fill-opacity="0.12" stroke="url(#brandG)" stroke-width="2"/>
              <path d="M32 18C32.8 18 33.5 18.7 33.5 19.5V28.5H42.5C43.3 28.5 44 29.2 44 30V34C44 34.8 43.3 35.5 42.5 35.5H33.5V44.5C33.5 45.3 32.8 46 32 46H28C27.2 46 26.5 45.3 26.5 44.5V35.5H17.5C16.7 35.5 16 34.8 16 34V30C16 29.2 16.7 28.5 17.5 28.5H26.5V19.5C26.5 18.7 27.2 18 28 18H32Z" fill="url(#brandG)" fill-opacity="0.9"/>
              <circle cx="18" cy="18" r="2.5" fill="#5B8CFF" fill-opacity="0.3"/>
              <circle cx="46" cy="18" r="2.5" fill="#7C4DFF" fill-opacity="0.3"/>
              <circle cx="18" cy="46" r="2.5" fill="#7C4DFF" fill-opacity="0.3"/>
              <circle cx="46" cy="46" r="2.5" fill="#5B8CFF" fill-opacity="0.3"/>
              <path d="M20 20L25 25" stroke="url(#brandG)" stroke-width="1" stroke-opacity="0.2" stroke-linecap="round"/>
              <path d="M44 20L39 25" stroke="url(#brandG)" stroke-width="1" stroke-opacity="0.2" stroke-linecap="round"/>
              <path d="M20 44L25 39" stroke="url(#brandG)" stroke-width="1" stroke-opacity="0.2" stroke-linecap="round"/>
              <path d="M44 44L39 39" stroke="url(#brandG)" stroke-width="1" stroke-opacity="0.2" stroke-linecap="round"/>
              <defs>
                <linearGradient id="brandG" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#4F8DFF"/>
                  <stop offset="100%" stop-color="#7C4DFF"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <p class="login-card-welcome">欢迎回来</p>
          <h2 class="login-card-title">登录您的账号</h2>
        </div>

        <el-tabs v-model="activeTab" class="login-tabs" :stretch="true">
          <el-tab-pane label="登录" name="login">
            <el-form :model="loginForm" label-position="top" class="login-form">
              <el-form-item label="用户名">
                <el-input
                  v-model="loginForm.username"
                  placeholder="请输入用户名"
                  :prefix-icon="User"
                  size="large"
                  class="premium-input"
                />
              </el-form-item>
              <el-form-item label="密码">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  :prefix-icon="Lock"
                  size="large"
                  class="premium-input"
                  @keyup.enter="handleLogin"
                />
              </el-form-item>
              <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleLogin">
                登录
              </el-button>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form :model="registerForm" label-position="top" class="login-form">
              <el-form-item label="用户名">
                <el-input
                  v-model="registerForm.username"
                  placeholder="请输入用户名"
                  :prefix-icon="User"
                  size="large"
                  class="premium-input"
                />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input
                  v-model="registerForm.email"
                  placeholder="选填（用于找回密码）"
                  :prefix-icon="Message"
                  size="large"
                  class="premium-input"
                />
              </el-form-item>
              <el-form-item label="密码">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="请设置密码（至少6位）"
                  :prefix-icon="Lock"
                  size="large"
                  class="premium-input"
                  @input="checkPasswordStrength"
                />
                <div class="password-strength" v-if="registerForm.password.length > 0">
                  <div class="strength-bar">
                    <div class="strength-fill" :class="strengthClass" :style="{ width: strengthPercent + '%' }"></div>
                  </div>
                  <span class="strength-label" :class="strengthClass">{{ strengthText }}</span>
                </div>
              </el-form-item>
              <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleRegister">
                注册
              </el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>
      <p class="login-footer">© 2026 AI Medical Consultant. All rights reserved.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/useUserStore'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('login')
const loading = ref(false)

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', password: '', email: '' })
const passwordScore = ref(0)

const strengthClass = computed(() => {
  if (passwordScore.value <= 1) return 'weak'
  if (passwordScore.value <= 2) return 'medium'
  return 'strong'
})
const strengthPercent = computed(() => {
  return (passwordScore.value / 4) * 100
})
const strengthText = computed(() => {
  if (passwordScore.value <= 1) return '弱'
  if (passwordScore.value <= 2) return '中'
  return '强'
})

function checkPasswordStrength() {
  const pwd = registerForm.password
  let score = 0
  if (pwd.length >= 6) score++
  if (pwd.length >= 10) score++
  if (/[A-Z]/.test(pwd) && /[a-z]/.test(pwd)) score++
  if (/\d/.test(pwd)) score++
  if (/[^A-Za-z0-9]/.test(pwd)) score++
  passwordScore.value = Math.min(score, 4)
}

async function handleLogin() {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  loading.value = true
  try {
    await userStore.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!registerForm.username || !registerForm.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  loading.value = true
  try {
    await userStore.register(registerForm.username, registerForm.password, registerForm.email)
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  min-height: 100vh;
  background: #0f0f23;
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ========= Left Brand Panel ========= */
.login-brand {
  flex: 1.2;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: linear-gradient(135deg, #1a1a3e 0%, #2d1b69 50%, #1a1a3e 100%);
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
}

.brand-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.wave {
  position: absolute;
  bottom: 0;
  width: 200%;
  height: 200px;
  background: rgba(79, 141, 255, 0.05);
  border-radius: 50% 50% 0 0;
  animation: waveMove 8s ease-in-out infinite;
}
.wave-1 { bottom: -20px; animation-duration: 8s; opacity: 0.3; background: rgba(79, 141, 255, 0.08); }
.wave-2 { bottom: -10px; animation-duration: 11s; opacity: 0.2; background: rgba(124, 77, 255, 0.06); }
.wave-3 { bottom: 0; animation-duration: 14s; opacity: 0.15; background: rgba(79, 141, 255, 0.04); }

@keyframes waveMove {
  0% { transform: translateX(0) scaleY(1); }
  25% { transform: translateX(-25%) scaleY(1.1); }
  50% { transform: translateX(-50%) scaleY(1); }
  75% { transform: translateX(-25%) scaleY(0.9); }
  100% { transform: translateX(0) scaleY(1); }
}

.brand-content {
  position: relative;
  z-index: 2;
  text-align: center;
  padding: 60px;
  max-width: 520px;
  animation: fadeInUp 1s ease-out;
}

.brand-logo {
  margin-bottom: 32px;
  filter: drop-shadow(0 0 30px rgba(79, 141, 255, 0.4));
  animation: float 6s ease-in-out infinite;
}

.brand-title {
  font-size: 36px;
  font-weight: 700;
  color: white;
  margin-bottom: 12px;
  letter-spacing: -0.5px;
}

.brand-subtitle {
  font-size: 15px;
  color: rgba(255,255,255,0.6);
  margin-bottom: 48px;
  line-height: 1.6;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: flex-start;
  max-width: 280px;
  margin: 0 auto;
}

.brand-feature {
  display: flex;
  align-items: center;
  gap: 12px;
  color: rgba(255,255,255,0.8);
  font-size: 14px;
  animation: fadeInUp 0.6s ease-out forwards;
  opacity: 0;
}
.brand-feature:nth-child(1) { animation-delay: 0.3s; }
.brand-feature:nth-child(2) { animation-delay: 0.5s; }
.brand-feature:nth-child(3) { animation-delay: 0.7s; }

/* ========= Right Form Panel ========= */
.login-form-panel {
  flex: 0.8;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f2f5 0%, #e8ecf5 100%);
  padding: 40px;
  position: relative;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: rgba(255,255,255,0.75);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 24px;
  padding: 40px 36px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.08);
  animation: slideUp 0.8s ease-out;
}

.login-card-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-card-logo {
  margin-bottom: 16px;
}

.login-card-welcome {
  font-size: 14px;
  color: #8E8E93;
  margin-bottom: 4px;
}

.login-card-title {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
}

.login-tabs {
  --el-tabs-header-height: 44px;
}
.login-tabs :deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 500;
  height: 44px;
  line-height: 44px;
  color: #8E8E93;
  transition: all 0.3s;
}
.login-tabs :deep(.el-tabs__item.is-active) {
  color: #4F8DFF;
  font-weight: 600;
}
.login-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(135deg, #4F8DFF, #7C4DFF);
  height: 3px;
  border-radius: 2px;
}

.login-form {
  margin-top: 8px;
}

/* Premium Input Styling */
.premium-input :deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 12px;
  box-shadow: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 4px 12px;
}
.premium-input :deep(.el-input__wrapper:hover) {
  background: rgba(255,255,255,0.75);
  border-color: rgba(255,255,255,0.5);
}
.premium-input :deep(.el-input__wrapper.is-focus) {
  background: rgba(255,255,255,0.9);
  border-color: #4F8DFF;
  box-shadow: 0 0 0 4px rgba(79, 141, 255, 0.1);
}
.premium-input :deep(.el-input__inner) {
  height: 44px;
  font-size: 14px;
}
.premium-input :deep(.el-input__prefix) {
  margin-right: 8px;
}
.premium-input :deep(.el-input__prefix-inner) .el-icon {
  font-size: 18px;
  color: #8E8E93;
  transition: color 0.3s;
}
.premium-input :deep(.el-input__wrapper.is-focus) .el-input__prefix-inner .el-icon {
  color: #4F8DFF;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}
.login-form :deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 500;
  color: #555;
  padding-bottom: 6px;
}

/* Password Strength */
.password-strength {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.strength-bar {
  flex: 1;
  height: 4px;
  background: rgba(0,0,0,0.06);
  border-radius: 2px;
  overflow: hidden;
}
.strength-fill {
  height: 100%;
  border-radius: 2px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.strength-fill.weak { background: #FF3B30; }
.strength-fill.medium { background: #FF9500; }
.strength-fill.strong { background: #34C759; }

.strength-label {
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}
.strength-label.weak { color: #FF3B30; }
.strength-label.medium { color: #FF9500; }
.strength-label.strong { color: #34C759; }

/* Login Button */
.login-btn {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  border: none;
  background: linear-gradient(135deg, #4F8DFF, #7C4DFF);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(79, 141, 255, 0.3);
  margin-top: 8px;
}
.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(79, 141, 255, 0.4);
}
.login-btn:active {
  transform: translateY(0);
}

.login-footer {
  margin-top: 24px;
  font-size: 12px;
  color: #B0B0B8;
  text-align: center;
}
</style>
