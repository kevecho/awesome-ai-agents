<template>
  <div class="records-page">
    <!-- Header -->
    <header class="records-header">
      <div class="records-header-left">
        <button class="back-btn" @click="$router.push('/')">
          <el-icon :size="20"><ArrowLeft /></el-icon>
          <span>返回首页</span>
        </button>
      </div>
      <div class="records-header-center">
        <svg width="28" height="28" viewBox="0 0 64 64" fill="none">
          <circle cx="32" cy="32" r="30" fill="url(#recG)" fill-opacity="0.1" stroke="url(#recG)" stroke-width="2"/>
          <rect x="21" y="16" width="22" height="34" rx="4" fill="url(#recG)" fill-opacity="0.1" stroke="url(#recG)" stroke-width="2" stroke-linecap="round"/>
          <path d="M26 24H38M26 30H38M26 36H32" stroke="url(#recG)" stroke-width="2.5" stroke-linecap="round"/>
          <circle cx="44" cy="20" r="2" fill="#FF9500" fill-opacity="0.3"/>
          <circle cx="20" cy="44" r="2" fill="#E68600" fill-opacity="0.3"/>
          <defs>
            <linearGradient id="recG" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#FF9500"/>
              <stop offset="100%" stop-color="#E68600"/>
            </linearGradient>
          </defs>
        </svg>
        <h3>我的病历</h3>
      </div>
      <div class="records-header-right"></div>
    </header>

    <!-- Main -->
    <main class="records-main">
      <!-- Stats -->
      <div class="records-stats" v-if="consultations.length > 0">
        <div class="records-stat-card">
          <div class="records-stat-icon" style="background: linear-gradient(135deg, #E8F4FD, #D0EAFC); color: #4F8DFF;">
            <el-icon :size="24"><Memo /></el-icon>
          </div>
          <div class="records-stat-info">
            <span class="records-stat-value">{{ consultations.length }}</span>
            <span class="records-stat-label">全部病历</span>
          </div>
        </div>
        <div class="records-stat-card">
          <div class="records-stat-icon" style="background: linear-gradient(135deg, #E8F8E8, #C8F0C8); color: #34C759;">
            <el-icon :size="24"><Clock /></el-icon>
          </div>
          <div class="records-stat-info">
            <span class="records-stat-value">{{ activeCount }}</span>
            <span class="records-stat-label">进行中</span>
          </div>
        </div>
      </div>

      <!-- Search -->
      <div class="records-search-section">
        <div class="search-box">
          <el-icon class="search-icon"><Search /></el-icon>
          <input
            v-model="searchQuery"
            placeholder="搜索病历标题..."
            class="search-input"
            @input="onSearchInput"
          />
          <button v-if="searchQuery" class="search-clear" @click="clearSearch">
            <el-icon><Close /></el-icon>
          </button>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="!loading && filteredConsultations.length === 0" class="empty-state">
        <div class="empty-illustration">
          <svg width="160" height="120" viewBox="0 0 160 120" fill="none">
            <rect x="20" y="30" width="120" height="80" rx="12" fill="#F0F6FF" stroke="#D0E0FF" stroke-width="2"/>
            <path d="M60 70 L70 60 L85 75 L100 55 L105 60" stroke="#4F8DFF" stroke-width="3" stroke-linecap="round"/>
            <circle cx="55" cy="55" r="3" fill="#4F8DFF"/>
            <circle cx="105" cy="50" r="3" fill="#4F8DFF"/>
          </svg>
        </div>
        <h4 v-if="searchQuery">未找到匹配的病历</h4>
        <h4 v-else>暂无病历记录</h4>
        <p v-if="searchQuery">尝试使用其他关键词搜索</p>
        <p v-else>点击「开始新问诊」体验 AI 医疗咨询</p>
      </div>

      <!-- Table -->
      <div v-else class="records-table-wrapper">
        <el-table :data="filteredConsultations" class="premium-table" style="width: 100%" v-loading="loading">
          <el-table-column prop="id" label="编号" width="140" align="center" />
          <el-table-column prop="title" label="标题" min-width="220" />
          <el-table-column prop="status" label="状态" width="130" align="center">
            <template #default="{ row }">
              <span :class="['status-tag', row.status]">
                <span class="status-dot"></span>
                {{ row.status === 'active' ? '进行中' : '已完成' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" min-width="220">
            <template #default="{ row }">
              <span class="time-text">{{ formatDate(row.updated_at) }}</span>
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
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Search, Close, Memo, Clock } from '@element-plus/icons-vue'
import api from '../api/index.js'

const router = useRouter()

const consultations = ref([])
const searchQuery = ref('')
const loading = ref(false)
let debounceTimer = null

const activeCount = computed(() =>
  consultations.value.filter(c => c.status === 'active').length
)

const filteredConsultations = computed(() => {
  if (!searchQuery.value.trim()) return consultations.value
  const q = searchQuery.value.trim().toLowerCase()
  return consultations.value.filter(c =>
    c.title.toLowerCase().includes(q) ||
    String(c.id).includes(q)
  )
})

function onSearchInput() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    fetchConsultations(searchQuery.value.trim() || null)
  }, 300)
}

function clearSearch() {
  searchQuery.value = ''
  fetchConsultations(null)
}

async function fetchConsultations(search = null) {
  loading.value = true
  try {
    const params = search ? { search } : {}
    const res = await api.get('/api/v1/consult/', { params })
    consultations.value = res.data
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchConsultations()
})
</script>

<style scoped>
.records-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #eef1f8 50%, #e8ecf5 100%);
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ========= Header ========= */
.records-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(20px);
  padding: 0 32px;
  height: 64px;
  border-bottom: 1px solid rgba(0,0,0,0.04);
  position: sticky;
  top: 0;
  z-index: 10;
}
.records-header-left, .records-header-right { flex: 1; }
.records-header-right {
  display: flex;
  justify-content: flex-end;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  font-size: 14px;
  color: #FF9500;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 10px;
  transition: all 0.2s;
}
.back-btn:hover { background: rgba(255,149,0,0.08); }

.records-header-center {
  display: flex;
  align-items: center;
  gap: 12px;
}
.records-header-center h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
}

/* ========= Main ========= */
.records-main {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 24px 60px;
}

/* ========= Stats ========= */
.records-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 28px;
}
.records-stat-card {
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
  transition: all 0.3s;
  animation: fadeInUp 0.5s ease-out;
}
.records-stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.06);
}
.records-stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.records-stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.records-stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
}
.records-stat-label {
  font-size: 13px;
  color: #8E8E93;
}

/* ========= Search ========= */
.records-search-section {
  margin-bottom: 28px;
}
.search-box {
  display: flex;
  align-items: center;
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.35);
  border-radius: 16px;
  padding: 4px 6px 4px 18px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.05);
  border: 2px solid transparent;
  transition: all 0.3s;
}
.search-box:focus-within {
  border-color: #FF9500;
  box-shadow: 0 0 0 4px rgba(255,149,0,0.08);
}
.search-icon {
  color: #8E8E93;
  font-size: 20px;
  margin-right: 12px;
  flex-shrink: 0;
}
.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 15px;
  padding: 14px 0;
  outline: none;
  color: #1a1a2e;
  font-family: inherit;
}
.search-input::placeholder { color: #b0b0b8; }
.search-clear {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border: none;
  background: #f0f2f5;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8E8E93;
  transition: all 0.2s;
}
.search-clear:hover { background: #e8ecf1; }

/* ========= Results Header ========= */
.results-header {
  margin-bottom: 16px;
}
.results-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
}
.results-count {
  font-size: 14px;
  font-weight: 400;
  color: #8E8E93;
}

/* ========= Table ========= */
.records-table-wrapper {
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.35);
  border-radius: 16px;
  padding: 4px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.05);
  overflow: hidden;
}

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
.premium-table :deep(.el-table__body tr:last-child td) {
  border-bottom: none;
}
.premium-table :deep(.el-table__row) {
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
  animation: rowSlideIn 0.4s ease-out both;
}
.premium-table :deep(.el-table__row:hover) {
  background: #f0f6ff !important;
  cursor: pointer;
}

@keyframes rowSlideIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

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
  outline: none;
}
.table-action-btn:focus {
  outline: none;
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
