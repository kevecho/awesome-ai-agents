<template>
  <div class="home-page">
    <!-- Premium Header -->
    <header class="app-header">
      <div class="header-left">
        <div class="brand-logo-mini">
          <svg width="32" height="32" viewBox="0 0 64 64" fill="none">
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
        <span class="brand-name">AI 智能问诊</span>
      </div>
      <div class="header-right">
        <el-popover placement="bottom-end" :width="280" trigger="click" popper-class="notif-popover">
          <template #reference>
            <el-badge :value="activeCount" :hidden="activeCount === 0" class="notification-badge">
              <el-button circle :icon="Bell" class="header-icon-btn" />
            </el-badge>
          </template>
          <div class="notif-panel">
            <div class="notif-panel-header">
              <span>进行中问诊</span>
              <span class="notif-panel-count">{{ totalActive }} 条</span>
            </div>
            <div class="notif-panel-list">
              <div v-for="item in activeList" :key="item.id" class="notif-panel-item" @click="goConsult(item.id)">
                <span class="notif-dot"></span>
                <div class="notif-info">
                  <span class="notif-title">{{ item.title }}</span>
                  <span class="notif-time">{{ formatTime(item.updated_at) }}</span>
                </div>
              </div>
              <div v-if="activeList.length === 0" class="notif-panel-empty">
                <el-icon :size="18"><Bell /></el-icon>
                <span>暂无进行中问诊</span>
              </div>
            </div>
            <div v-if="totalActive > 5" class="notif-panel-footer" @click="$router.push('/records')">
              更多记录
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>
        </el-popover>
        <el-dropdown trigger="click">
          <div class="user-avatar">
            <span class="avatar-text">{{ userStore.username?.charAt(0).toUpperCase() || 'U' }}</span>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleLogout">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- Main Content -->
    <main class="app-main">
      <!-- Welcome Section -->
      <section class="welcome-section">
        <div class="welcome-particles">
          <span class="particle" v-for="i in 6" :key="i" :style="{ '--x': particleX[i], '--d': (1 + i * 0.4) + 's', '--s': (0.5 + i * 0.2) + 'rem' }">+</span>
          <span class="particle pulse" style="--x: 80%; --d: 3s; --s: 0.8rem">&#9829;</span>
          <span class="particle pulse" style="--x: 15%; --d: 4.5s; --s: 0.6rem">&#10013;</span>
        </div>
        <div class="welcome-glow"></div>
        <div class="welcome-text">
          <div class="welcome-badge">
            <span class="badge-dot"></span>
            {{ greeting }}
          </div>
          <h1 class="welcome-title">
            <span class="title-highlight">您好，{{ userStore.username }}</span>
          </h1>
          <p class="welcome-subtitle">
            <span class="typing-text">{{ subtitleText }}</span>
            <span v-if="typingActive" class="cursor-blink">|</span>
          </p>
          <div class="welcome-actions">
            <button class="welcome-btn primary" @click="startNewConsult">
              <el-icon><Plus /></el-icon>
              <span>开始新问诊</span>
            </button>
            <button class="welcome-btn secondary" @click="scrollToConsultHistory">
              <el-icon><Clock /></el-icon>
              <span>查看记录</span>
            </button>
          </div>
        </div>
      </section>

      <!-- Stats Cards -->
      <section class="stats-grid">
        <div class="stat-card" v-for="(stat, i) in stats" :key="i" :style="{ animationDelay: (0.1 + i * 0.1) + 's' }">
          <div class="stat-icon" :style="{ background: stat.bg }">
            <el-icon :size="22" :color="stat.color"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value gradient-num">{{ stat.value }}</span>
            <span class="stat-label">{{ stat.label }}</span>
          </div>
          <div v-if="stat.trend > 0" class="stat-trend up">
            <template v-if="i === 0">已完成 {{ stat.trend }}</template>
            <template v-else>{{ stat.trend }}%</template>
          </div>
        </div>
      </section>

      <!-- Quick Actions -->
      <section class="quick-actions">
        <div class="section-header">
          <h3>快捷操作</h3>
        </div>
        <div class="actions-grid">
          <div class="action-card" @click="startNewConsult">
            <div class="action-icon" style="background: linear-gradient(135deg, #4F8DFF 0%, #3A6FD9 100%);">
              <el-icon :size="24" color="white"><Plus /></el-icon>
            </div>
            <span class="action-label">开始新问诊</span>
            <span class="action-desc">描述症状，获取 AI 分析</span>
          </div>
          <div class="action-card" @click="$router.push('/knowledge')">
            <div class="action-icon" style="background: linear-gradient(135deg, #34C759 0%, #28A745 100%);">
              <el-icon :size="24" color="white"><Document /></el-icon>
            </div>
            <span class="action-label">知识库</span>
            <span class="action-desc">查阅医学资料</span>
          </div>
          <div class="action-card" @click="$router.push('/records')">
            <div class="action-icon" style="background: linear-gradient(135deg, #FF9500 0%, #E68600 100%);">
              <el-icon :size="24" color="white"><Memo /></el-icon>
            </div>
            <span class="action-label">我的病历</span>
            <span class="action-desc">查看问诊记录</span>
          </div>
<!-- 
          <div class="action-card">
            <div class="action-icon" style="background: linear-gradient(135deg, #7C4DFF 0%, #651FFF 100%);">
              <el-icon :size="24" color="white"><TrendCharts /></el-icon>
            </div>
            <span class="action-label">健康建议</span>
            <span class="action-desc">个性化健康指导</span>
          </div>
          -->
        </div>
      </section>

      <!-- Consultation History -->
      <section id="consult-history" class="consult-section">
        <div class="section-header">
          <h3>问诊记录</h3>
          <span class="section-count" v-if="consultations.length > 0">共 {{ consultations.length }} 条</span>
        </div>

        <!-- Empty State -->
        <div v-if="consultations.length === 0" class="empty-state">
          <div class="empty-illustration">
            <svg width="160" height="120" viewBox="0 0 160 120" fill="none">
              <rect x="20" y="30" width="120" height="80" rx="12" fill="#F0F6FF" stroke="#D0E0FF" stroke-width="2"/>
              <path d="M60 70 L70 60 L85 75 L100 55 L105 60" stroke="#4F8DFF" stroke-width="3" stroke-linecap="round"/>
              <circle cx="55" cy="55" r="3" fill="#4F8DFF"/>
              <circle cx="105" cy="50" r="3" fill="#4F8DFF"/>
            </svg>
          </div>
          <h4>暂无问诊记录</h4>
          <p>点击「开始新问诊」体验 AI 医疗咨询</p>
        </div>

        <!-- Table -->
        <div v-else class="consult-table-wrapper">
          <el-table :data="consultations" class="premium-table" style="width: 100%">
            <el-table-column prop="id" label="编号" width="120" align="center" />
            <el-table-column prop="title" label="标题" min-width="200" />
            <el-table-column prop="status" label="状态" width="120" align="center">
              <template #default="{ row }">
                <span :class="['status-tag', row.status]">
                  <span class="status-dot"></span>
                  {{ row.status === 'active' ? '进行中' : '已完成' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="updated_at" label="更新时间" min-width="220">
              <template #default="{ row }">
                <span class="time-text">{{ new Date(row.updated_at).toLocaleString('zh-CN') }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button size="small" class="table-action-btn" @click="$router.push(`/consult/${row.id}`)">
                  {{ row.status === 'completed' ? '查看记录' : '进入问诊' }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/useUserStore'
import { useConsultStore } from '../stores/useConsultStore'
import { Plus, Document, Memo, TrendCharts, Bell, SwitchButton, Clock, ArrowRight } from '@element-plus/icons-vue'
import api from '../api/index.js'

const router = useRouter()
const userStore = useUserStore()
const consultStore = useConsultStore()

const creating = ref(false)
const consultations = ref([])

const stats = reactive([
  { label: '问诊总数', value: '--', icon: 'Memo', bg: 'linear-gradient(135deg, #E8F4FD 0%, #D0EAFC 100%)', color: '#4F8DFF', trend: 0 },
  { label: '进行中', value: '--', icon: 'Clock', bg: 'linear-gradient(135deg, #E8F8E8 0%, #C8F0C8 100%)', color: '#34C759', trend: 0 },
  { label: '知识库', value: '--', icon: 'Document', bg: 'linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%)', color: '#FF9500', trend: 0 },
])

const activeCount = computed(() => consultations.value.filter(c => c.status === 'active').length)

const activeList = computed(() => consultations.value.filter(c => c.status === 'active').slice(0, 5))
const totalActive = computed(() => consultations.value.filter(c => c.status === 'active').length)

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '上午好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const subtitleText = ref('')
const typingActive = ref(true)
const fullSubtitle = '我是您的小医助手，有什么不舒服请随时告诉我'
const particleX = ref(Array.from({length: 7}, () => Math.random() * 80 + 10 + '%'))

onMounted(async () => {
  if (!userStore.isLoggedIn) {
    router.push('/login')
    return
  }
  await userStore.fetchUser()
  await Promise.all([loadConsultations(), loadKnowledgeStats()])
  typeSubtitle()
})

function typeSubtitle() {
  let i = 0
  const timer = setInterval(() => {
    if (i <= fullSubtitle.length) {
      subtitleText.value = fullSubtitle.slice(0, i)
      i++
    } else {
      clearInterval(timer)
      typingActive.value = false
    }
  }, 45)
}

async function loadConsultations() {
  try {
    await consultStore.fetchConsultations()
    consultations.value = consultStore.consultations
    const total = consultations.value.length
    const active = consultations.value.filter(c => c.status === 'active').length
    const completed = total - active
    stats[0].value = total
    stats[0].trend = completed
    stats[1].value = active
    stats[1].trend = total > 0 ? Math.round(active / total * 100) : 0
  } catch {
    // handled
  }
}

async function loadKnowledgeStats() {
  try {
    const res = await api.get('/api/v1/knowledge/stats')
    stats[2].value = res.data.total_documents
  } catch {
    // handled
  }
}

async function startNewConsult() {
  creating.value = true
  try {
    const data = await consultStore.createConsultation()
    router.push(`/consult/${data.id}`)
  } catch {
    // handled
  } finally {
    creating.value = false
  }
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return month + '-' + day + ' ' + hour + ':' + min
}

function goConsult(id) {
  router.push('/consult/' + id)
}

function scrollToConsultHistory() {
  const el = document.getElementById('consult-history')
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #eef1f8 50%, #e8ecf5 100%);
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ========= Premium Header ========= */
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 0 32px;
  height: 64px;
  border-bottom: 1px solid rgba(0,0,0,0.04);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-logo-mini {
  display: flex;
  align-items: center;
}

.brand-name {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #4F8DFF, #7C4DFF);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-icon-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: linear-gradient(135deg, #f5f7fa 0%, #eef1f8 50%, #e8ecf5 100%);
  border-radius: 10px;
  font-size: 18px;
  transition: all 0.3s;
}
.header-icon-btn:hover {
  background: #e8ecf1;
}

.notification-badge :deep(.el-badge__content) {
  background: #FF3B30;
  border: 2px solid white;
  font-size: 10px;
  height: 18px;
  min-width: 18px;
  line-height: 14px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #4F8DFF, #7C4DFF);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}
.user-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 15px rgba(79,141,255,0.3);
}
.avatar-text {
  color: white;
  font-size: 16px;
  font-weight: 600;
}

/* ========= Main ========= */
.app-main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 24px 60px;
}

/* ========= Welcome Section ========= */
.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 240px;
  background: linear-gradient(135deg, #4F8DFF 0%, #667eea 30%, #764ba2 100%);
  background-size: 200% 200%;
  border-radius: 24px;
  padding: 48px 56px;
  margin-bottom: 32px;
  position: relative;
  overflow: hidden;
  animation: fadeInUp 0.6s ease-out, gradientShift 12s ease infinite;
}
.welcome-section::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 30%, rgba(255,255,255,0.06) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(255,255,255,0.04) 0%, transparent 50%);
}

/* Floating particles */
.welcome-particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  overflow: hidden;
}
.particle {
  position: absolute;
  top: -5%;
  left: var(--x, 50%);
  font-size: var(--s, 0.6rem);
  color: rgba(255,255,255,0.15);
  animation: particleFall var(--d, 3s) ease-in infinite;
  animation-delay: calc(var(--i, 0) * 0.5s);
}
.particle.pulse {
  animation: particlePulse var(--d, 4s) ease-in-out infinite;
}

@keyframes particleFall {
  0% { transform: translateY(-20%) rotate(0deg); opacity: 0; }
  10% { opacity: 0.25; }
  90% { opacity: 0.15; }
  100% { transform: translateY(2600%) rotate(720deg); opacity: 0; }
}
@keyframes particlePulse {
  0%, 100% { opacity: 0.05; transform: scale(0.8); }
  50% { opacity: 0.2; transform: scale(1.2); }
}

/* Glow overlay */
.welcome-glow {
  position: absolute;
  top: -50%;
  right: -20%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
  animation: glowPulse 4s ease-in-out infinite;
}
@keyframes glowPulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.15); opacity: 1; }
}

.welcome-text {
  position: relative;
  z-index: 2;
  flex: 1;
}

/* Badge */
.welcome-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 16px;
  background: rgba(255,255,255,0.12);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 20px;
  font-family: 'Outfit', 'Inter', sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: rgba(255,255,255,0.9);
  margin-bottom: 16px;
  letter-spacing: 0.3px;
}
.badge-dot {
  width: 6px;
  height: 6px;
  background: #34C759;
  border-radius: 50%;
  animation: badgePulse 2s ease-in-out infinite;
}
@keyframes badgePulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(52,199,89,0.4); }
  50% { opacity: 0.7; box-shadow: 0 0 0 4px rgba(52,199,89,0); }
}

/* Title */
.welcome-title {
  margin-bottom: 10px;
}
.title-highlight {
  font-family: 'Outfit', 'Inter', sans-serif;
  font-size: 32px;
  font-weight: 700;
  color: white;
  letter-spacing: -0.3px;
  text-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

/* Subtitle with typing */
.welcome-subtitle {
  font-family: 'Inter', 'PingFang SC', sans-serif;
  font-size: 15px;
  color: rgba(255,255,255,0.7);
  margin-bottom: 28px;
  min-height: 1.6em;
}
.typing-text {
  background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.6));
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.cursor-blink {
  color: rgba(255,255,255,0.7);
  animation: blink 0.8s step-end infinite;
  font-weight: 300;
}
@keyframes blink {
  50% { opacity: 0; }
}

/* Welcome actions */
.welcome-actions {
  display: flex;
  gap: 12px;
}
.welcome-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 12px;
  border: none;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
}
.welcome-btn.primary {
  background: white;
  color: #4F8DFF;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}
.welcome-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(0,0,0,0.15);
}
.welcome-btn.secondary {
  background: rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.85);
  border: 1px solid rgba(255,255,255,0.2);
}
.welcome-btn.secondary:hover {
  background: rgba(255,255,255,0.18);
  transform: translateY(-2px);
}
/* ========= Stats Grid ========= */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.35);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.05);
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  animation: fadeInUp 0.6s ease-out forwards;
  opacity: 0;
  position: relative;
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.stat-value {
  font-size: 24px;
  font-weight: 800;
  font-family: 'Outfit', 'Inter', sans-serif;
  background: linear-gradient(135deg, #1a1a2e, #4F8DFF);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.5px;
}
.stat-label {
  font-size: 13px;
  color: #8E8E93;
}

.stat-trend {
  position: absolute;
  right: 20px;
  top: 20px;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
}
.stat-trend.up { background: #E8F8E8; color: #34C759; }
.stat-trend.down { background: #FFF0F0; color: #FF3B30; }

/* ========= Quick Actions ========= */
.quick-actions {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.section-header h3 {
  font-size: 20px;
  font-weight: 700;
  font-family: 'Outfit', 'Inter', sans-serif;
  color: #1a1a2e;
  letter-spacing: -0.2px;
}
.section-count {
  font-size: 13px;
  color: #8E8E93;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.action-card {
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.35);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  box-shadow: 0 8px 32px rgba(0,0,0,0.05);
  animation: fadeInUp 0.6s ease-out forwards;
  opacity: 0;
}
.action-card:nth-child(1) { animation-delay: 0.1s; }
.action-card:nth-child(2) { animation-delay: 0.2s; }
.action-card:nth-child(3) { animation-delay: 0.3s; }
.action-card:nth-child(4) { animation-delay: 0.4s; }

.action-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 16px 40px rgba(0,0,0,0.12);
}

.action-icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
}

.action-label {
  display: block;
  font-size: 16px;
  font-weight: 700;
  font-family: 'Outfit', 'Inter', sans-serif;
  color: #1a1a2e;
  margin-bottom: 4px;
  letter-spacing: -0.2px;
}

.action-desc {
  font-size: 12px;
  color: #8E8E93;
}

/* ========= Consult Section ========= */
.consult-section {
  animation: fadeInUp 0.6s ease-out;
  animation-delay: 0.3s;
}

.consult-table-wrapper {
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.35);
  border-radius: 16px;
  padding: 4px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.05);
  overflow: hidden;
}

/* Premium Table */
.premium-table :deep(.el-table__inner-wrapper)::before {
  display: none;
}
.premium-table :deep(.el-table__header th) {
  background: linear-gradient(135deg, #f4f7ff 0%, #f8f9fc 100%);
  color: #1a1a2e;
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0.4px;
  border-bottom: 1px solid #e8ecf1;
  padding: 14px 12px;
  font-family: 'Outfit', 'Inter', sans-serif;
}
.premium-table :deep(.el-table__header th:first-child) {
  padding-left: 20px;
}
.premium-table :deep(.el-table__row) {
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
  animation: rowSlideIn 0.4s ease-out both;
}
.premium-table :deep(.el-table__row:hover) {
  background: #f0f6ff !important;
  cursor: pointer;
}
.premium-table :deep(.el-table__body tr) {
  border-bottom: 1px solid #f0f2f5;
}
.premium-table :deep(.el-table__body tr:last-child td) {
  border-bottom: none;
}
.premium-table :deep(.el-table__body td) {
  border-bottom: 1px solid #f3f5f8;
  padding: 16px 12px;
  font-size: 13.5px;
  color: #444;
}
.premium-table :deep(.el-table__body td:first-child) {
  padding-left: 20px;
}
.premium-table :deep(.el-table__body td:last-child) {
  padding-right: 16px;
}

@keyframes rowSlideIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Status Tags */
.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}
.status-tag.active {
  background: linear-gradient(135deg, #E8F8E8, #D0F0D0);
  color: #2E7D32;
}
.status-tag.completed {
  background: linear-gradient(135deg, #E8F4FD, #D0EAFC);
  color: #1E6EA0;
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}
.status-tag.active .status-dot { background: #34C759; }
.status-tag.completed .status-dot { background: #4F8DFF; }

.time-text {
  font-size: 13px;
  color: #666;
}

.table-action-btn {
  border-radius: 8px;
  font-weight: 500;
  padding: 6px 16px;
  background: linear-gradient(135deg, #4F8DFF, #7C4DFF);
  color: white;
  border: none;
  transition: all 0.3s;
}
.table-action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79,141,255,0.3);
}

/* ========= Empty State ========= */
.empty-state {
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.35);
  border-radius: 16px;
  padding: 60px 40px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0,0,0,0.05);
}
.empty-illustration {
  margin-bottom: 20px;
  animation: float 6s ease-in-out infinite;
}
.empty-state h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 8px;
}
.empty-state p {
  font-size: 14px;
  color: #8E8E93;
}
</style>
<style>
/* Notification Popover */
.notif-popover {
  padding: 0 !important;
  border-radius: 16px !important;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(0,0,0,0.10) !important;
  border: 1px solid rgba(0,0,0,0.04) !important;
}
.notif-panel {
  display: flex;
  flex-direction: column;
}
.notif-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  font-family: 'Outfit', 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  border-bottom: 1px solid #f0f2f5;
}
.notif-panel-count {
  font-size: 12px;
  font-weight: 400;
  color: #8E8E93;
}
.notif-panel-list {
  max-height: 320px;
  overflow-y: auto;
}
.notif-panel-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f5f5f5;
}
.notif-panel-item:last-child {
  border-bottom: none;
}
.notif-panel-item:hover {
  background: #f5f8ff;
}
.notif-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #34C759;
  flex-shrink: 0;
  animation: notifPulse 2s ease-in-out infinite;
}
@keyframes notifPulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(52,199,89,0.4); }
  50% { opacity: 0.7; box-shadow: 0 0 0 4px rgba(52,199,89,0); }
}
.notif-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}
.notif-title {
  font-size: 13px;
  font-weight: 500;
  color: #1a1a2e;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notif-time {
  font-size: 11px;
  color: #8E8E93;
}
.notif-panel-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px 18px;
  color: #b0b0b8;
  font-size: 13px;
}
.notif-panel-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 12px 18px;
  border-top: 1px solid #f0f2f5;
  font-size: 13px;
  font-weight: 500;
  color: #4F8DFF;
  cursor: pointer;
  transition: background 0.2s;
}
.notif-panel-footer:hover {
  background: #f5f8ff;
}
</style>