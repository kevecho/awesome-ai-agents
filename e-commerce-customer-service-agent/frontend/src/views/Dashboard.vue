<template>
  <div class="dashboard-page">
    <header class="page-header">
      <el-button text @click="router.push('/')">返回对话</el-button>
      <h2>数据看板</h2>
    </header>
    <div class="dashboard-content">
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">--</div><div class="stat-label">总会话量</div></div>
        <div class="stat-card"><div class="stat-value">--</div><div class="stat-label">今日会话</div></div>
        <div class="stat-card"><div class="stat-value">--%</div><div class="stat-label">AI 解决率</div></div>
        <div class="stat-card"><div class="stat-value">--%</div><div class="stat-label">转人工率</div></div>
      </div>
      <el-empty description="接入数据库后，此处将展示运营数据看板。" />
    </div>
  </div>
</template>
<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>
<style scoped>
.dashboard-page { max-width: 1200px; margin: 0 auto; min-height: 100vh; background: #fff; padding: 20px; }
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px; }
.stat-card { padding: 24px; background: #f8f9fa; border-radius: 12px; text-align: center; }
.stat-value { font-size: 28px; font-weight: 700; color: #667eea; margin-bottom: 4px; }
.stat-label { font-size: 13px; color: #909399; }
</style>
