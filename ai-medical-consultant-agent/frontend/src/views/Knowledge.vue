<template>
  <div class="knowledge-page">
    <!-- Header -->
    <header class="kb-header">
      <div class="kb-header-left">
        <button class="back-btn" @click="$router.push('/')">
          <el-icon :size="20"><ArrowLeft /></el-icon>
          <span>返回首页</span>
        </button>
      </div>
      <div class="kb-header-center">
        <svg width="28" height="28" viewBox="0 0 64 64" fill="none">
          <circle cx="32" cy="32" r="30" fill="url(#kbG)" fill-opacity="0.1" stroke="url(#kbG)" stroke-width="2"/>
          <path d="M16 20C16 18.9 16.9 18 18 18H32V46H18C16.9 46 16 45.1 16 44V20Z" fill="url(#kbG)" fill-opacity="0.1" stroke="url(#kbG)" stroke-width="2" stroke-linecap="round"/>
          <path d="M48 20C48 18.9 47.1 18 46 18H32V46H46C47.1 46 48 45.1 48 44V20Z" fill="url(#kbG)" fill-opacity="0.1" stroke="url(#kbG)" stroke-width="2" stroke-linecap="round"/>
          <path d="M28 28H36M28 34H36" stroke="url(#kbG)" stroke-width="2.5" stroke-linecap="round"/>
          <circle cx="20" cy="20" r="2" fill="#34C759" fill-opacity="0.3"/>
          <circle cx="44" cy="44" r="2" fill="#28A745" fill-opacity="0.3"/>
          <defs>
            <linearGradient id="kbG" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#34C759"/>
              <stop offset="100%" stop-color="#28A745"/>
            </linearGradient>
          </defs>
        </svg>
        <h3>医学知识库</h3>
      </div>
      <div class="kb-header-right">
        <el-button class="add-knowledge-btn" @click="showDrawer = true">
          <el-icon><Plus /></el-icon> 添加知识
        </el-button>
      </div>
    </header>

    <!-- Main -->
    <main class="kb-main">
      <!-- Stats Cards -->
      <div class="kb-stats" v-if="stats">
        <div class="kb-stat-card">
          <div class="kb-stat-icon" style="background: linear-gradient(135deg, #E8F4FD, #D0EAFC); color: #4F8DFF;">
            <el-icon :size="24"><Document /></el-icon>
          </div>
          <div class="kb-stat-info">
            <span class="kb-stat-value">{{ stats.total_documents }}</span>
            <span class="kb-stat-label">知识库文档</span>
          </div>
        </div>
        <div class="kb-stat-card">
          <div class="kb-stat-icon" style="background: linear-gradient(135deg, #E8F8E8, #C8F0C8); color: #34C759;">
            <el-icon :size="24"><Connection /></el-icon>
          </div>
          <div class="kb-stat-info">
            <span class="kb-stat-value">{{ stats.vector_count }}</span>
            <span class="kb-stat-label">向量索引</span>
          </div>
        </div>
      </div>

      <!-- Search -->
      <div class="kb-search-section">
        <div class="search-box">
          <el-icon class="search-icon"><Search /></el-icon>
          <input
            v-model="searchQuery"
            placeholder="搜索医学知识（例如：感冒、高血压、糖尿病）"
            class="search-input"
            @keyup.enter="handleSearch"
          />
          <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''; clearSearch()">
            <el-icon><Close /></el-icon>
          </button>
        </div>
        <div class="search-hints" v-if="!searchResults.length && !searching">
          <span class="hint-label">热门搜索：</span>
          <span class="hint-tag" @click="searchQuery = '感冒'; handleSearch()">感冒</span>
          <span class="hint-tag" @click="searchQuery = '高血压'; handleSearch()">高血压</span>
          <span class="hint-tag" @click="searchQuery = '糖尿病'; handleSearch()">糖尿病</span>
          <span class="hint-tag" @click="searchQuery = '失眠'; handleSearch()">失眠</span>
        </div>
      </div>

      <!-- Search Results Table -->
      <div class="kb-results" v-if="searchResults.length > 0">
        <div class="results-header">
          <h4>搜索结果 <span class="results-count">({{ searchResults.length }} 条)</span></h4>
          <el-button text size="small" @click="clearSearch">返回全部</el-button>
        </div>
        <div class="kb-table-wrapper">
          <el-table
            :data="searchResults"
            class="premium-table"
            style="width: 100%"
            row-key="id"
          >
            <el-table-column type="expand">
              <template #default="{ row }">
                <div class="expand-content" v-html="renderMd(row.content)"></div>
              </template>
            </el-table-column>
            <el-table-column label="序号" width="80" align="center">
              <template #default="{ $index }">{{ $index + 1 }}</template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <el-tooltip :content="row.title" placement="top-start" :hide-after="0" :show-after="400" effect="light">
                  <span class="cell-text">{{ row.title }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="120" align="center">
              <template #default="{ row }">
                <span :class="['category-tag', row.category]">{{ categoryLabel(row.category) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="content" label="内容摘要" min-width="300">
              <template #default="{ row }">
                <el-popover
                  placement="top-start"
                  :width="520"
                  trigger="hover"
                  :hide-after="100"
                  :enterable="false"
                  popper-class="content-popover"
                >
                  <template #reference>
                    <span class="content-preview">{{ truncate(row.content, 80) }}</span>
                  </template>
                  <div class="popover-body">{{ row.content }}</div>
                </el-popover>
              </template>
            </el-table-column>
            <el-table-column prop="score" label="相关性" width="100" align="center">
              <template #default="{ row }">
                <span class="score-text" v-if="row.score">{{ (row.score * 100).toFixed(0) }}%</span>
                <span class="score-text" v-else>--</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- All Documents Table -->
      <div class="kb-results" v-if="!searchResults.length && !searching && allItems.length > 0">
        <div class="results-header">
          <h4>全部知识 <span class="results-count">({{ total }} 条)</span></h4>
        </div>
        <div class="kb-table-wrapper">
          <el-table
            ref="tableRef"
            :data="allItems"
            class="premium-table"
            style="width: 100%"
            row-key="id"
          >
            <el-table-column type="expand">
              <template #default="{ row }">
                <div class="expand-content" v-html="renderMd(row.content)"></div>
              </template>
            </el-table-column>
            <el-table-column label="序号" width="80" align="center">
              <template #default="{ $index }">{{ (currentPage - 1) * pageSize + $index + 1 }}</template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <el-tooltip :content="row.title" placement="top-start" :hide-after="0" :show-after="400" effect="light">
                  <span class="cell-text">{{ row.title }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="120" align="center">
              <template #default="{ row }">
                <span :class="['category-tag', row.category]">{{ categoryLabel(row.category) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="content" label="内容摘要" min-width="300">
              <template #default="{ row }">
                <el-popover
                  placement="top-start"
                  :width="520"
                  trigger="hover"
                  :hide-after="100"
                  :enterable="false"
                  popper-class="content-popover"
                >
                  <template #reference>
                    <span class="content-preview">{{ truncate(row.content, 80) }}</span>
                  </template>
                  <div class="popover-body">{{ row.content }}</div>
                </el-popover>
              </template>
            </el-table-column>
            <el-table-column prop="source" label="来源" width="150" show-overflow-tooltip>
              <template #default="{ row }">
                <el-tooltip :content="row.source" placement="top-start" :hide-after="0" :show-after="400" effect="light">
                  <span class="cell-text">{{ row.source || '--' }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                <span class="time-text">{{ formatTime(row.created_at) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <div class="action-btns">
                  <el-button size="small" class="table-action-btn" @click="viewDetail(row)">
                    详情
                  </el-button>
                  <el-button size="small" class="table-delete-btn" @click="handleDelete(row)">
                    删除
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- Pagination -->
        <div class="kb-pagination-wrapper" v-if="total > pageSize">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="onPageSizeChange"
            @current-change="onPageChange"
            background
          />
        </div>
      </div>

      <!-- Empty State -->
      <div class="empty-state" v-if="!searchResults.length && !searching && allItems.length === 0 && loaded">
        <div class="empty-icon">
          <el-icon :size="48"><Document /></el-icon>
        </div>
        <h4>知识库暂无内容</h4>
        <p>点击右上角「添加知识」按钮，添加第一条医学知识吧</p>
      </div>

      <!-- Loading State -->
      <div v-if="searching" class="loading-state">
        <div class="skeleton-card" v-for="i in 3" :key="i">
          <div class="skeleton-shimmer" style="height: 20px; width: 60%; margin-bottom: 12px;"></div>
          <div class="skeleton-shimmer" style="height: 14px; width: 100%; margin-bottom: 8px;"></div>
          <div class="skeleton-shimmer" style="height: 14px; width: 80%;"></div>
        </div>
      </div>
    </main>

    <!-- Add Knowledge Drawer -->
    <el-drawer
      v-model="showDrawer"
      title="添加医学知识"
      size="480px"
      class="knowledge-drawer"
    >
      <el-form :model="addForm" label-position="top">
        <el-form-item label="标题">
          <el-input v-model="addForm.title" placeholder="例如：普通感冒、高血压..." size="large" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="addForm.category" placeholder="选择分类" size="large" style="width: 100%;">
            <el-option label="疾病知识" value="disease" />
            <el-option label="药品说明" value="drug" />
            <el-option label="检查指标" value="exam" />
            <el-option label="临床指南" value="guideline" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="addForm.content"
            type="textarea"
            :rows="10"
            placeholder="请输入医学知识内容..."
            size="large"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDrawer = false">取消</el-button>
        <el-button type="primary" :loading="adding" @click="handleAddKnowledge">
          添加到知识库
        </el-button>
      </template>
    </el-drawer>

    <!-- Detail Dialog -->
    <el-dialog v-model="detailVisible" :title="detailDoc?.title || '文档详情'" width="700px" top="5vh">
      <div class="detail-category" v-if="detailDoc">
        <span :class="['category-tag', detailDoc.category]">{{ categoryLabel(detailDoc.category) }}</span>
        <span class="detail-source" v-if="detailDoc.source">来源：{{ detailDoc.source }}</span>
        <span class="detail-time" v-if="detailDoc.created_at">{{ formatTime(detailDoc.created_at) }}</span>
      </div>
      <div class="detail-body" v-if="detailDoc" v-html="renderMd(detailDoc.content)"></div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ArrowLeft, Plus, Search, Close, Document, Connection } from '@element-plus/icons-vue'
import api from '../api/index.js'
import MarkdownIt from 'markdown-it'
import { ElMessage, ElMessageBox } from 'element-plus'

const md = new MarkdownIt({ breaks: true, html: true })

const tableRef = ref(null)
const stats = ref(null)
const allItems = ref([])
const total = ref(0)
const loaded = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const adding = ref(false)
const showDrawer = ref(false)
const detailVisible = ref(false)
const detailDoc = ref(null)

const addForm = ref({ title: '', category: '', content: '' })

onMounted(async () => {
  await Promise.all([loadStats(), loadDocuments()])
})

async function loadStats() {
  try {
    const res = await api.get('/api/v1/knowledge/stats')
    stats.value = res.data
  } catch { /* ignore */ }
}

async function loadDocuments() {
  try {
    const res = await api.get('/api/v1/knowledge/documents', {
      params: { page: currentPage.value, page_size: pageSize.value }
    })
    allItems.value = res.data.items || []
    total.value = res.data.total || 0
  } catch {
    allItems.value = []
    total.value = 0
  } finally {
    loaded.value = true
  }
}

function onPageChange(page) {
  currentPage.value = page
  loadDocuments()
}

function onPageSizeChange(size) {
  pageSize.value = size
  currentPage.value = 1
  loadDocuments()
}

function clearSearch() {
  searchQuery.value = ''
  searchResults.value = []
  loadDocuments()
}

async function handleSearch() {
  if (!searchQuery.value.trim()) return
  searching.value = true
  try {
    const res = await api.post('/api/v1/knowledge/search', {
      query: searchQuery.value,
      top_k: 20,
    })
    searchResults.value = res.data
  } catch { /* ignore */ }
  finally { searching.value = false }
}

async function handleAddKnowledge() {
  if (!addForm.value.title || !addForm.value.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  adding.value = true
  try {
    await api.post('/api/v1/knowledge/documents', addForm.value)
    ElMessage.success('知识已添加')
    addForm.value = { title: '', category: '', content: '' }
    showDrawer.value = false
    await Promise.all([loadStats(), loadDocuments()])
  } catch { /* ignore */ }
  finally { adding.value = false }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除「${row.title}」吗？此操作将同时从数据库和向量索引中移除该文档，不可恢复。`,
      '删除确认',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return // 用户取消
  }
  try {
    await api.delete(`/api/v1/knowledge/documents/${row.id}`)
    ElMessage.success('已删除')
    await Promise.all([loadStats(), loadDocuments()])
  } catch { /* error handled by interceptor */ }
}

function viewDetail(row) {
  detailDoc.value = row
  detailVisible.value = true
}

function categoryLabel(value) {
  const map = { disease: '疾病知识', drug: '药品说明', exam: '检查指标', guideline: '临床指南' }
  return map[value] || value
}

function truncate(text, maxLen) {
  if (!text) return ''
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
}

function formatTime(t) {
  if (!t) return '--'
  return new Date(t).toLocaleString('zh-CN')
}

function renderMd(text) {
  return md.render(text || '')
}
</script>

<style scoped>
/* ========= Cell Text Truncation ========= */
.cell-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.knowledge-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #eef1f8 50%, #e8ecf5 100%);
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ========= Header ========= */
.kb-header {
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

.kb-header-left, .kb-header-right { flex: 1; }
.kb-header-right { display: flex; justify-content: flex-end; }

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  font-size: 14px;
  color: #4F8DFF;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 10px;
  transition: all 0.2s;
}
.back-btn:hover { background: rgba(79,141,255,0.08); }

.kb-header-center {
  display: flex;
  align-items: center;
  gap: 12px;
}
.kb-header-center h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
}

.add-knowledge-btn {
  border-radius: 10px;
  background: linear-gradient(135deg, #34C759, #28A745);
  color: white;
  border: none;
  padding: 10px 20px;
  font-weight: 500;
  transition: all 0.3s;
}
.add-knowledge-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(52,199,89,0.3);
  color: white;
}

/* ========= Main ========= */
.kb-main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 24px 60px;
}

/* ========= Stats ========= */
.kb-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 28px;
}

.kb-stat-card {
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
.kb-stat-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.06); }

.kb-stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kb-stat-info { display: flex; flex-direction: column; gap: 2px; }
.kb-stat-value { font-size: 28px; font-weight: 700; color: #1a1a2e; }
.kb-stat-label { font-size: 13px; color: #8E8E93; }

/* ========= Search ========= */
.kb-search-section { margin-bottom: 28px; }

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
.search-box:focus-within { border-color: #4F8DFF; box-shadow: 0 0 0 4px rgba(79,141,255,0.08); }

.search-icon { color: #8E8E93; font-size: 20px; margin-right: 12px; flex-shrink: 0; }

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

.search-hints { display: flex; align-items: center; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
.hint-label { font-size: 13px; color: #8E8E93; }
.hint-tag {
  padding: 4px 14px;
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 20px;
  font-size: 12px;
  color: #555;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #eee;
}
.hint-tag:hover { border-color: #4F8DFF; color: #4F8DFF; background: rgba(79,141,255,0.04); }

/* ========= Results Header ========= */
.kb-results { margin-bottom: 24px; }
.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.results-header h4 { font-size: 16px; font-weight: 600; color: #1a1a2e; margin: 0; }
.results-count { font-size: 14px; font-weight: 400; color: #8E8E93; }

/* ========= Table Wrapper ========= */
.kb-table-wrapper {
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.35);
  border-radius: 16px;
  padding: 4px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.05);
  overflow: hidden;
}

/* ========= Premium Table ========= */
.premium-table :deep(.el-table__inner-wrapper)::before { display: none; }
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
.premium-table :deep(.el-table__header th:first-child) { padding-left: 20px; }
.premium-table :deep(.el-table__row) {
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
}
.premium-table :deep(.el-table__row:hover) {
  background: #f0f6ff !important;
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
.premium-table :deep(.el-table__body td:first-child) { padding-left: 20px; }
.premium-table :deep(.el-table__body td:last-child) { padding-right: 16px; }

/* ========= Expand Content ========= */
.expand-content {
  padding: 16px 24px;
  font-size: 14px;
  line-height: 1.8;
  color: #444;
  max-height: 360px;
  overflow-y: auto;
  background: #f9fafc;
  border-radius: 8px;
  margin: 4px 0;
}
.expand-content :deep(p) { margin: 0 0 10px; }
.expand-content :deep(p:last-child) { margin-bottom: 0; }
.expand-content :deep(h1), .expand-content :deep(h2), .expand-content :deep(h3) {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 12px 0 6px;
}
.expand-content :deep(ul), .expand-content :deep(ol) { padding-left: 20px; margin: 6px 0; }
.expand-content :deep(li) { margin-bottom: 4px; }
.expand-content :deep(code) {
  background: #eef1f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
.expand-content :deep(blockquote) {
  border-left: 3px solid #4F8DFF;
  padding-left: 12px;
  color: #666;
  margin: 8px 0;
}

/* ========= Category Tags ========= */
.category-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}
.category-tag.disease { background: #FFF3E0; color: #E65100; }
.category-tag.drug { background: #E8F4FD; color: #1565C0; }
.category-tag.exam { background: #E8F8E8; color: #2E7D32; }
.category-tag.guideline { background: #F3E5F5; color: #7B1FA2; }

/* ========= Content Preview ========= */
.content-preview { color: #888; font-size: 13px; }
.time-text { color: #888; font-size: 13px; }
.score-text { font-weight: 600; color: #4F8DFF; font-size: 13px; }

/* ========= Table Action Buttons ========= */
.action-btns {
  display: flex;
  gap: 8px;
  align-items: center;
}
.table-action-btn {
  border-radius: 8px;
  font-weight: 500;
  padding: 5px 12px;
  font-size: 12px;
  color: #4F8DFF;
  border-color: #4F8DFF;
  background: transparent;
  transition: all 0.2s;
  white-space: nowrap;
}
.table-action-btn:hover {
  color: white;
  background: #4F8DFF;
  border-color: #4F8DFF;
}

.table-delete-btn {
  border-radius: 8px;
  font-weight: 500;
  padding: 5px 12px;
  font-size: 12px;
  color: #E53935;
  border-color: #E53935;
  background: transparent;
  transition: all 0.2s;
}
.table-delete-btn:hover {
  color: white;
  background: #E53935;
  border-color: #E53935;
}

/* ========= Pagination ========= */
.kb-pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 16px 0;
}
.kb-pagination-wrapper :deep(.el-pagination) {
  --el-pagination-bg-color: rgba(255,255,255,0.72);
  --el-pagination-button-bg-color: rgba(255,255,255,0.9);
  padding: 8px 20px;
  border-radius: 12px;
  backdrop-filter: blur(12px);
}

/* ========= Detail Dialog ========= */
.detail-category {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}
.detail-source { font-size: 13px; color: #888; }
.detail-time { font-size: 13px; color: #888; margin-left: auto; }
.detail-body {
  font-size: 14px;
  line-height: 1.8;
  color: #444;
  max-height: 60vh;
  overflow-y: auto;
}
.detail-body :deep(p) { margin: 0 0 10px; }
.detail-body :deep(h1), .detail-body :deep(h2), .detail-body :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 14px 0 8px;
}
.detail-body :deep(ul), .detail-body :deep(ol) { padding-left: 20px; margin: 8px 0; }
.detail-body :deep(li) { margin-bottom: 4px; }

/* ========= Loading Skeleton ========= */
.loading-state { display: flex; flex-direction: column; gap: 12px; }
.skeleton-card {
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.35);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.05);
}

/* ========= Empty State ========= */
.empty-state { text-align: center; padding: 64px 24px; }
.empty-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: #b0b0b8;
  margin-bottom: 20px;
}
.empty-state h4 { font-size: 17px; font-weight: 600; color: #555; margin: 0 0 8px; }
.empty-state p { font-size: 14px; color: #8E8E93; margin: 0; }

/* ========= Drawer ========= */
.knowledge-drawer :deep(.el-drawer__header) {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 8px;
  padding: 24px 24px 0;
}
.knowledge-drawer :deep(.el-drawer__body) { padding: 8px 24px 24px; }
.knowledge-drawer :deep(.el-form-item__label) { font-size: 13px; font-weight: 500; color: #555; }
</style>

<style>
/* 全局 popover 样式 — popper-class 不受 scoped 影响 */
.content-popover {
  max-height: 360px;
  padding: 12px 16px !important;
}
.content-popover .popover-body {
  font-size: 13px;
  line-height: 1.8;
  color: #333;
  max-height: 330px;
  overflow-y: auto;
  white-space: pre-wrap !important;
  word-break: break-word;
}
.content-popover .popover-body :deep(p) { margin: 0 0 8px; }
.content-popover .popover-body :deep(p:last-child) { margin-bottom: 0; }
</style>
